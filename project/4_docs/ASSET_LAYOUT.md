# Ripped asset layout (`assets/`), format 1

Owner: agent-build (Agent 1). Consumers: the virtual NitroFS (Agent 3), the generator (Agent 2), users.
Produced by `mkds_builder <rom.nds> --rip --out DIR` (and by `--build`, which rips first). Generated on the user's machine from
their ROM; never distribute it. Deterministic: the same ROM always gives byte-identical files and `manifest.json`.

```
DIR/assets/
  README.txt                 "generated from your ROM, do not distribute"
  manifest.json              everything below, with sizes and SHA-256
  files/<NitroFS path>       every named file at its original path, e.g. files/data/Course/cross_course.carc
  system/
    header.bin               NDS header (0x200 bytes)
    arm9.bin                 ARM9 binary exactly as stored in the ROM (may be compressed; the lifter decompresses)
    arm7.bin                 ARM7 binary exactly as stored
    arm9_overlay_table.bin   ARM9 overlay table (y9), 32-byte records
    arm7_overlay_table.bin   ARM7 overlay table (y7), may be empty
    fnt.bin                  file name table (directory tree, names, first file id per directory)
    fat.bin                  original file allocation table (start/end per file id; offsets are the ROM's, for provenance)
    banner.bin               icon/title banner
    overlays/arm9_ov_NNN.bin ARM9 overlay files (FAT entries referenced by the y9 table; they have no NitroFS name)
    overlays/arm7_ov_NNN.bin ARM7 overlay files (if any)
    unnamed/fat_NNNNN.bin    any other FAT entry without a name (expected: none)
```

## manifest.json
```json
{
  "format": "mkds-assets", "format_version": 1,
  "rom": {"sha256": "...", "game_code": "AMCE", "revision": 0, "size": 33554432},
  "fat_entries": 606, "fnt_directories": 123,
  "system": {"header.bin": {"size": 512, "sha256": "..."}, ...},
  "files": [
    {"id": 0, "kind": "arm9_overlay", "overlay": 0, "path": "system/overlays/arm9_ov_000.bin", "size": 123, "sha256": "..."},
    {"id": 57, "kind": "file", "name": "data/Course/cross_course.carc", "path": "files/data/Course/cross_course.carc", "size": 0, "sha256": "..."}
  ],
  "assets_sha256": "..."
}
```
- `files` holds **one entry per FAT id**, sorted by `id`. `kind` is `file` (named; `name` = NitroFS path), `arm9_overlay` / `arm7_overlay`
  (`overlay` = overlay id) or `unnamed`. `path` is relative to `assets/`, always `/`-separated.
- The game opens files by FAT id as well as by name, so a rebuilt filesystem must give every file the **same id**; the FNT in
  `system/fnt.bin` already encodes names -> ids, so a virtual NitroFS can reuse it unchanged and only needs a new FAT pointing at the
  loose files.
- `assets_sha256` = SHA-256 over the lines `"{id} {sha256}\n"` for every entry in id order, then `"{name} {sha256}\n"` for every system
  file in name order. The launcher/runtime compares it to detect edited or missing assets.
- Names are validated when ripping: no `..`, no absolute paths, no `\`, `:` or control characters (a hostile ROM cannot write outside `assets/`).

## Launch contract (builder <-> runtime)
- The bundle manifest (`manifest.json`, format 4+) has `"assets": {"path": "assets", "format_version", "files", "assets_sha256",
  "manifest_sha256"}`. `play` re-hashes every listed file (`mkds_builder::rip::verify`) before each launch and refuses to start on
  any missing/edited file.
- `launch_args` placeholders substituted by `play`: `{rom}` = the hash-verified ROM path, `{assets}` = the bundle's `assets/` dir.
- Today the generated game is launched with `["{rom}"]` (the runtime still reads the ROM). When Agent 3's virtual NitroFS lands, the
  runtime accepts `--assets <dir>` and the builder switches to `["--assets", "{assets}"]`; from then on the ROM is not opened at run
  time (the launcher may still check its hash for provenance).
