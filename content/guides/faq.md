# Frequently asked questions
<!-- Start here -->

## Is Driftlift an emulator?
The normal game statically compiles CPU instructions rather than interpreting them during play. The established baseline still models DS memory, peripherals and timing. Experimental native services replace parts of that hardware model. A reference interpreter remains for tests.

## Is the source fully readable now?
All 12,736 functions have raised output, but inferred types and confident names are incomplete. Plain signatures and directly callable loops remain polish goals. See [pipeline](pipeline.md).

## Where is the ROM or ready-to-play download?
Neither is supplied. Own the game, dump your cartridge lawfully and build locally. Do not share ROMs, extracted files, generated game source or compiled bundles. The project does not grant rights to Nintendo material, and the reviewed checkout has no top-level project license declaration.

## Can I mod it?
You can study/rebuild your local generated workspace and use [texture replacement](textures.md). Manifest verification can reject changes to packaged files. Keep original game material private. More hooks are planned.

## Should I turn native mode on?
It remains experimental and opt-in. Leave toggles off for the established baseline. The launcher exposes only FS/ARM7/time, not SND or build-time native timing. [Modes](modes.md) explains the difference.

## Does frame-equal mean every mode matches real hardware?
No. These are regression comparisons with the exact model, on specified routes, using pinned seeds and justified masks. Menus have transition differences and battle diverges after lag. See [verification](verify.md).

## Is it 28% faster everywhere?
The latest paired acceptance measurement reports about 28% less CPU per frame on one tested setup. It is not a universal speed guarantee. Display resolution does not change physics; high-refresh interpolation and widescreen camera changes remain future work.

## What platforms and copies work?
The supported ROM is clean USA AMCE revision 0. Windows is primary; Linux has limited validation and macOS is untested. Other regions and games are not established compatible.

## What should a bug report include?
OS, error text, scenario and relevant logs; the launcher saves launcher-build.log. Do not attach ROMs, assets, generated source or built games. Check [status](status.md) for known work.

Sources: [README](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/README.md), [launcher](../sources/launcher.md), [defaults evidence](../sources/BLOCK5_DEFAULTS.md).
