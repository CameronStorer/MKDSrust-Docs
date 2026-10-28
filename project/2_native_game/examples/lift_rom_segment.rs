//! Small user-ROM lift entry point. Generated game code is local output only.
//! Usage: lift_rom_segment ROM arm7|arm9 NEW_OUTPUT entry:byte_size [...]
//! Entries are supplied metadata; this tool does not guess boundaries or modes.
use recomp::lift::{self, Image};
use std::io::Write;

fn number(text: &str) -> Result<u32, Box<dyn std::error::Error>> {
    Ok(if let Some(hex) = text.strip_prefix("0x") { u32::from_str_radix(hex, 16)? } else { text.parse()? })
}
fn header(rom: &[u8], at: usize) -> Result<u32, Box<dyn std::error::Error>> {
    Ok(u32::from_le_bytes(rom.get(at..at+4).ok_or("truncated ROM header")?.try_into()?))
}
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() < 4 { return Err("usage: ROM arm7|arm9 NEW_OUTPUT entry:byte_size [...]".into()); }
    let rom = std::fs::read(&args[0])?;
    let segment = args[1].to_str().ok_or("segment must be UTF-8")?;
    let (base, image) = match segment {
        "arm7" => {
            let offset = header(&rom, 0x30)? as usize;
            let size = header(&rom, 0x3c)? as usize;
            let end = offset.checked_add(size).ok_or("ARM7 range overflow")?;
            (header(&rom, 0x38)?, rom.get(offset..end).ok_or("ARM7 outside ROM")?.to_vec())
        }
        "arm9" => (header(&rom, 0x28)?, mkds_builder::extract::arm9_main(&rom)?),
        _ => return Err("expected arm7 or arm9; other loaded segments require their own image metadata".into()),
    };
    let img = Image::new(base, &image);
    let mut output = String::from("// @generated from user ROM. Do not commit or distribute.\n");
    let mut table = String::from("pub static LIFTED: &[recomp::mem::Lifted] = &[\n");
    let mut seen = std::collections::BTreeSet::new();
    for arg in &args[3..] {
        let (entry, size) = arg.to_str().ok_or("entry metadata must be UTF-8")?.split_once(':').ok_or("entry needs :size")?;
        let entry = number(entry)?;
        let size = number(size)?;
        if !seen.insert(entry) { return Err("duplicate entry".into()); }
        let low = entry & !1;
        let high = low.checked_add(size).ok_or("function span overflow")?;
        let offset = low.checked_sub(base).ok_or("entry below image")? as usize;
        if size == 0 || offset.checked_add(size as usize).is_none_or(|end| end > image.len()) { return Err("function outside image".into()); }
        if entry & 1 == 0 && low % 4 != 0 { return Err("unaligned ARM entry (Thumb entries use bit0)".into()); }
        let f = lift::discover(&img, entry, Some((low, high)), 10000)?;
        if !f.undecoded.is_empty() { return Err(format!("undecoded instructions at {:?}", f.undecoded).into()); }
        let id = format!("{entry:08X}");
        output.push_str(&lift::emit(&f, &id));
        table.push_str(&format!("recomp::mem::Lifted {{ segment: \"{segment}\", entry: {entry}, blocks: BLOCKS_{id}, insts: INSTS_{id}, f: f_{id} }},\n"));
        eprintln!("Lifted {entry:#010X}: {} instructions, {} blocks", f.insts.len(), f.blocks.len());
    }
    table.push_str("];\n");
    output.push_str(&table);
    let mut file = std::fs::OpenOptions::new().write(true).create_new(true).open(&args[2])?;
    file.write_all(output.as_bytes())?;
    Ok(())
}
fn main() {
    if let Err(error) = run() { eprintln!("Lift failed: {error}"); std::process::exit(1); }
}
