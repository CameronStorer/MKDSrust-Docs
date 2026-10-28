//! Boot harness (T069): load the user's ROM into the DS memory model, run the ARM9 entry point on the
//! lifted code (interpreter fallback) with an instruction budget, and report what stopped it and which
//! services the game asked for that nothing implements yet. The ranked report tells the lanes
//! (L3 hardware, L5 SDK/OS, L6 GX, L7 sound) what to build next.
//!
//! `cargo run --release --example mkds_boot -- [budget_millions]`   (ROM: `MKDS_ROM`, default ../gamefile.nds)
include!(concat!(env!("OUT_DIR"), "/lifted.rs"));

use recomp::dispatch::Dispatcher;
use recomp::ds_mem::Bus;
use recomp::machine::Machine;
use recomp::rt::{Bus as RtBus, Cpu, Mem};
use std::collections::HashMap;

/// Runs calls inline (a call is a jump) so the harness loop sees every instruction of every callee.
struct Tracer<'a, 'b> {
    m: &'b mut Machine<'a>,
    calls: HashMap<u32, u64>,
    /// HLE'd functions (entry address, bit 0 ignored) -> value returned in r0.
    hooks: HashMap<u32, u32>,
}
impl Mem for Tracer<'_, '_> {
    fn r8(&mut self, a: u32) -> u8 { self.m.r8(a) }
    fn r16(&mut self, a: u32) -> u16 { self.m.r16(a) }
    fn r32(&mut self, a: u32) -> u32 { self.m.r32(a) }
    fn w8(&mut self, a: u32, v: u8) { self.m.w8(a, v) }
    fn w16(&mut self, a: u32, v: u16) { self.m.w16(a, v) }
    fn w32(&mut self, a: u32, v: u32) { self.m.w32(a, v) }
}
impl RtBus for Tracer<'_, '_> {
    fn call(&mut self, _c: &mut Cpu, target: u32, _ret: u32) -> u32 {
        *self.calls.entry(target).or_insert(0) += 1;
        if let Some(&v) = self.hooks.get(&(target & !1)) {
            _c.r[0] = v;
            return _ret;
        }
        target
    }
    fn swi(&mut self, c: &mut Cpu, n: u32) { self.m.swi(c, n) }
    fn mrc(&mut self, c: &mut Cpu, cp: u8, o1: u8, n: u8, cm: u8, o2: u8) -> u32 { self.m.mrc(c, cp, o1, n, cm, o2) }
    fn mcr(&mut self, c: &mut Cpu, cp: u8, o1: u8, n: u8, cm: u8, o2: u8, v: u32) { self.m.mcr(c, cp, o1, n, cm, o2, v) }
}

/// Return address that no code uses: the call "finishes" if the entry point ever returns to it.
const SENTINEL: u32 = 0xFFFF_FF00;
/// Where the HLE'd BIOS IRQ stub "returns" to once the game's handler (address in DTCM `0x027E3FFC`) is done.
const IRQ_RETURN: u32 = 0xFFFF_FE00;



fn main() {
    let budget_m: u32 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(20);
    let rom_path = std::env::var("MKDS_ROM").unwrap_or_else(|_| concat!(env!("CARGO_MANIFEST_DIR"), "/../gamefile.nds").into());
    let rom = std::fs::read(&rom_path).unwrap_or_else(|e| {
        eprintln!("cannot read ROM {rom_path}: {e}");
        std::process::exit(2);
    });
    let sections = mkds_builder::extract::arm9_sections(&rom).expect("ARM9 sections");
    let entry = u32::from_le_bytes(rom[0x24..0x28].try_into().unwrap());

    let mut hw = Bus::new();
    for s in &sections {
        for (i, &b) in s.data.iter().enumerate() {
            hw.w8(s.ram_address.wrapping_add(i as u32), b);
        }
        println!("loaded {:<22} {:#010X} +{:#X} (bss {:#X})", s.name, s.ram_address, s.data.len(), s.bss_size);
    }
    let disp = Dispatcher::new(LIFTED);
    // crt0 runs the in-place BLZ decompressor when the module params' compressed_static_end (+0x14) is non-zero.
    // The builder hands us the already-decompressed image, so clear it as the real boot code does after unpacking.
    if let Some(main) = sections.iter().find(|s| s.name == "arm9_main") {
        let magic = [0x21u8, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21];
        if let Some(p) = main.data.windows(8).take(0x8000).position(|w| w == magic) {
            let params = main.ram_address + p as u32 - 0x1C;
            println!("module params at {params:#010X}; clearing compressed_static_end");
            hw.w32(params + 0x14, 0);
        }
    }
    hw.arm7_announce_ready();
    let mut machine = Machine::new(hw, &disp);
    let mut m = Tracer { m: &mut machine, calls: HashMap::new(), hooks: HashMap::new() };

    let mut c = Cpu::default();
    c.r[13] = 0x027E_0000; // the SDK start-up code sets up its own stacks; this is only a safe default
    c.r[14] = SENTINEL;
    c.budget = budget_m.saturating_mul(1_000_000);
    let start = c.budget;
    println!("entry {entry:#010X}, budget {budget_m}M instructions, {} lifted functions", LIFTED.len());
    // Step the entry point ourselves (calls still go through the machine: hooks, lifted code, fallback) so we
    // see every pc and can advance hardware time: 2 ARM9 instructions ~ 1 bus cycle.
    // HLE of SDK services the ARM7/hardware would answer. Each line says what the replaced function is.
    //   sub_215122C: CARD backup-memory command (PXI tag 4, SPI flash/EEPROM state machine): report success
    m.hooks.insert(0x0215_122C, 1);
    m.hooks.insert(0x0215_119C, 1); // CARD backup verify: read flash, memcmp with the expected bytes -> pretend equal
    m.hooks.insert(0x0215_1288, 1); // its state machine (commands 1-7); callers other than sub_215122C
    let mut pc = entry;
    let mut hist: std::collections::HashMap<u32, u64> = std::collections::HashMap::new();
    let mut steps = 0u64;
    let mut stop = String::new();
    let mut acked = 0usize;
    let mut recent = std::collections::VecDeque::<u32>::new();
    let mut irqs_taken = 0u64;
    let r = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        while c.budget > 0 {
            if pc == SENTINEL {
                stop = "entry point returned".into();
                return;
            }
            // generic ARM7 stand-in: acknowledge every word the ARM9 sent with an empty reply on the same tag
            // (refine per tag once the ARM9's receive callback for that tag has been read)
            while acked < m.m.hw.ipc_out.len() {
                let w = m.m.hw.ipc_out[acked];
                acked += 1;
                if w & 0x1F != 0 {
                    m.m.hw.arm7_send(w & 0x1F);
                }
            }
            if pc == IRQ_RETURN {
                // end of the BIOS IRQ stub: ldmfd sp!, {r0-r3, r12, lr}; subs pc, lr, #4 (CPSR <- SPSR)
                let sp = c.r[13];
                for (i, r) in [0usize, 1, 2, 3, 12, 14].into_iter().enumerate() {
                    c.r[r] = m.r32(sp + 4 * i as u32);
                }
                c.r[13] = sp + 24;
                let back = c.r[14].wrapping_sub(4);
                let thumb = c.restore_spsr();
                pc = if thumb { back | 1 } else { back };
                continue;
            }
            if c.ctl & 0x80 == 0 && m.m.hw.irq_pending() {
                // IRQ entry as the CPU does it, then the BIOS stub: push {r0-r3, r12, lr}, lr = the stub's
                // return, jump to the game's handler (address kept in DTCM at 0x027E3FFC)
                let handler = m.r32(0x027E_3FFC);
                if handler != 0 {
                    c.exception(0x12, (pc & !1).wrapping_add(4), pc & 1 != 0);
                    let sp = c.r[13].wrapping_sub(24);
                    for (i, r) in [0usize, 1, 2, 3, 12, 14].into_iter().enumerate() {
                        m.w32(sp + 4 * i as u32, c.r[r]);
                    }
                    c.r[13] = sp;
                    c.r[14] = IRQ_RETURN;
                    irqs_taken += 1;
                    pc = handler;
                    continue;
                }
            }
            let d = recomp::interp::fetch(&mut m, pc);
            *hist.entry(pc).or_insert(0) += 1;
            c.budget -= 1;
            steps += 1;
            let next = recomp::interp::exec(&d, pc, &mut c, &mut m);
            if steps % 2 == 0 {
                m.m.hw.advance(1);
            }
            if next.wrapping_sub(pc) > 8 && pc.wrapping_sub(next) > 8 {
                if recent.len() == 40 {
                    recent.pop_front();
                    recent.pop_front();
                }
                recent.push_back(pc);
                recent.push_back(next);
            }
            pc = next;
        }
        stop = "instruction budget exhausted".into();
    }));
    if let Err(e) = r {
        let msg = e.downcast_ref::<String>().cloned().or_else(|| e.downcast_ref::<&str>().map(|s| s.to_string())).unwrap_or_default();
        stop = format!("panic: {msg}");
    }
    let used = start - c.budget;
    println!("\n== stop ==");
    println!("{stop} after {used} instructions, at pc {pc:#010X}");
    println!("lr {:#010X}  sp {:#010X}  r0 {:#X}  r1 {:#X}  r2 {:#X}  r3 {:#X}", c.r[14], c.r[13], c.r[0], c.r[1], c.r[2], c.r[3]);
    let (iflag, ie, ime) = (m.m.hw.r32(0x0400_0214), m.m.hw.r32(0x0400_0210), m.m.hw.r32(0x0400_0208));
    println!("hw cycles {}  scanline {}  IF {iflag:#X}  IE {ie:#X}  IME {ime}", m.m.hw.cycles, m.m.hw.line);
    let mut top: Vec<_> = hist.iter().collect();
    top.sort_by(|a, b| b.1.cmp(a.1));
    println!("last jumps (from -> to): {}", recent.iter().collect::<Vec<_>>().chunks(2).map(|c| format!("{:#X}->{:#X}", c[0], c[1])).collect::<Vec<_>>().join("  "));
    println!("\n== hottest pcs (spin loops show here) ==");
    for (a, n) in top.iter().take(12) {
        println!("{n:>9}  {a:#010X}");
    }
    println!("interrupts delivered: {irqs_taken}");
    println!("distinct pcs executed: {}   distinct call targets: {}", hist.len(), m.calls.len());
    let mut calls: Vec<_> = m.calls.iter().map(|(a, n)| (*a, *n)).collect();
    calls.sort_by(|a, b| b.1.cmp(&a.1));
    println!("
== most-called targets ==");
    for (a, n) in calls.iter().take(12) {
        println!("{n:>9}  {a:#010X}");
    }
    let (gx, ipc) = (m.m.hw.gx.len(), m.m.hw.ipc_out.len());
    println!("
== words the ARM9 sent to the ARM7 (PXI: tag = bits 0-4, err = bit 5, data = bits 6-31) ==");
    for w in m.m.hw.ipc_out.iter().take(32) {
        println!("{w:#010X}  tag {:>2}  err {}  data {:#X}", w & 0x1F, (w >> 5) & 1, w >> 6);
    }
    drop(m);

    println!("\n== unhandled services (count) ==");
    let mut un: Vec<_> = machine.unhandled.iter().collect();
    un.sort_by(|a, b| b.1.cmp(a.1).then(a.0.cmp(b.0)));
    for (what, n) in un.iter().take(40) {
        println!("{n:>8}  {what}");
    }
    if un.is_empty() {
        println!("(none)");
    }
    println!("\n== hook hits ==");
    let mut hh: Vec<_> = machine.hook_hits.iter().collect();
    hh.sort();
    for (a, n) in hh {
        println!("{a:#010X}  x{n}");
    }
    println!("\n3D port writes logged: {}   IPC words sent: {}", gx, ipc);
}
