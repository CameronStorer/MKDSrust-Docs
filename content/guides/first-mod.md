# Making your first mod
<!-- Modders -->

A mod is a small zip: a `manifest.json`, **patches** for game files you changed and any **new** files you made. It never contains the game's own files, so anyone can share it, and every player applies it to their own copy. The MKDSrust launcher does all of the packaging for you.

You need the launcher with a built game (Setup) and your own Mario Kart DS (USA, revision 0) ROM.

## 1. Create a mod project

In the launcher open **Mods → Create mod…**. Enter a name, your author name and a type (character, kart, track, battle, music, texture, gameplay or other). The mod id is filled in for you (`author.mod-name`); it must stay the same for every version of your mod.

Keep **Unpack .carc/.narc archives into folders** ticked. The launcher creates a project folder in `%APPDATA%\MKDSrust\modding\<id>\` and opens it:

| Path | What it is |
|---|---|
| `romfs/` | A copy of the files from **your** ROM. Edit these. |
| `romfs/…/<name>.carc.unpacked/` | An archive, unpacked. Edit the files inside; the archive is rebuilt when you pack. |
| `manifest.json` | Name, version, type, author, license and description of your mod. |
| `package/` | Optional `README.md` and up to 8 preview images (`.png`, `.jpg`, `.webp`) for your mod's page. |
| `README.md` | A short reminder of all of this. |

The project folder holds game files from your ROM: keep it on your PC and share only the packed zip.

The same works from a terminal:
~~~powershell
mkds_builder mod create --rom "C:\Games\my-copy.nds" --name "My First Mod" --author me --type other --extract --root "$env:APPDATA\MKDSrust\modding"
~~~

## 2. Change something

Any DS tool that edits files in place works. Good first changes:

- **Text** (`.bmg` message files): change a menu label with a BMG editor such as Kuriimu2. Keep the text length similar at first.
- **2D graphics** (`.nclr` palettes, `.ncgr`/`.nscr` images): NitroPaint or Tinke.
- **Models and textures** (`.nsbmd`, `.nsbtx`): a NSBMD exporter for Blender or the MKDS Course Modifier. See also [replacing textures](textures.md).
- **Courses** (`.nkm`, `.kcl`) and **sound** (`.sdat`, `.sseq`, `.swar`, `.strm`): course editors, Nitro Studio 2 or VGMTrans.

You can also add brand-new files anywhere under `romfs/` if they use one of the [allowed DS formats](#what-a-package-may-contain). Deleting a file does nothing: the original stays.

## 3. Test in game

Back on the Mods page, find your project under **Your mod projects** and press **Test in game**. The launcher packs your changes, installs them as `<id>.dev` at the bottom of the load order (so they win over every other mod), starts the game, and removes the test copy when you close it. Edit, test, repeat.

If something does not show up, open **Advanced → Open logs**: `logs/game.log` lists every file a mod changed (`[mods] <id>: applied <file>`) and every mod that was skipped, with the reason.

## 4. Pack and share

Press **Pack** (or run `mkds_builder mod pack "<project folder>"`). The launcher compares `romfs/` with your ROM:

- changed files become binary patches (bsdiff) against the original file,
- new allowed files are added as they are,
- unchanged files are left out.

Archives are rebuilt with as few changed bytes as possible, so a one-word text change in a compressed archive becomes a patch of a few hundred bytes. The zip is then checked with exactly the same rules mkdsrust.com uses for uploads, and the report lists every patch and added file. The result is in `modding\packages\<id>-<version>.zip`, ready to upload at [mkdsrust.com](https://mkdsrust.com/upload).

For a new release, raise `version` in `manifest.json` (for example `1.0.0` to `1.1.0`) and pack again.

## Installing mods

Players install mods in three ways: **Install with MKDSrust** on a mod's page (the browser opens the launcher, which downloads, checks and installs it), dropping a mod zip onto the launcher window, or **Install .zip…** on the Mods page.

All mods share **one load order**. Tick a mod to turn it on, drag it (or use ▲▼) to move it: when two mods change the same file, the one lower in the list wins. A warning on a mod shows how many files overlap with other mods, and hovering it lists which mod wins each file. The filter chips show one type at a time.

## What a package may contain

Only formats the game reads, plus package metadata. The file extension must match its contents.

| Group | Extensions |
|---|---|
| Models and animation | `.nsbmd` `.nsbtx` `.nsbca` `.nsbta` `.nsbtp` `.nsbma` `.nsbva` |
| 2D graphics | `.nclr` `.ncgr` `.nscr` `.ncer` `.nanr` |
| Archives | `.narc` `.carc` (contents are checked with the same rules) |
| Sound | `.sdat` `.sseq` `.sbnk` `.swar` `.strm` |
| Text | `.bmg` |
| Course | `.kcl` `.nkm` |
| Package | `manifest.json`, top-level `README.md`/`README.txt`, up to 8 preview images, `.bsdiff` patches |

Added files must be your own work: files that are identical or nearly identical to a game file are rejected, and existing game files can only be changed with a patch. Mods are never applied in Accuracy mode or in the exact-timing reference runs, and setting `MKDS_NO_MODS=1` starts the game without any mods.

Next: [replace textures](textures.md) · [accuracy and native modes](modes.md) · [build and explore](modders.md).
