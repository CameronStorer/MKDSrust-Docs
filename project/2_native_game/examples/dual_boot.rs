//! Two-CPU boot probe (T070) with the functions this build lifted (MKDS_LIFT_CAP): see `recomp::boot`.
//!
//! `cargo run --release --example dual_boot -- [budget_millions]`   (ROM: `MKDS_ROM`, default ../gamefile.nds)
include!(concat!(env!("OUT_DIR"), "/lifted.rs"));

fn main() {
    let budget_m: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(50);
    let rom_path = std::env::var("MKDS_ROM").unwrap_or_else(|_| concat!(env!("CARGO_MANIFEST_DIR"), "/../gamefile.nds").into());
    let rom = std::fs::read(&rom_path).unwrap_or_else(|e| {
        eprintln!("cannot read ROM {rom_path}: {e}");
        std::process::exit(2);
    });
    let image = mkds_builder::extract::arm9_main(&rom).expect("ARM9 binary");
    recomp::boot::probe(&rom, image, LIFTED, budget_m);
}
