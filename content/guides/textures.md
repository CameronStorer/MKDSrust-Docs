# Replace textures locally
<!-- Modders -->

The GPU renderer can dump textures from your own game and load PNG replacements.

1. Open settings.txt beside controls.txt (%APPDATA%\MKDS Native Builder on Windows).
2. Set DumpTextures = C:\MKDS textures\dump and play. Each texture is saved once as an ID-named PNG.
3. Edit selected PNGs, retaining filenames. Each replacement must be the original dimensions multiplied by a whole number from 1 through 8: a 64 by 32 image can become 256 by 128.
4. Put replacements in a pack folder, set TexturePack = C:\MKDS textures\pack and clear DumpTextures = to stop dumping.
5. Launch again and inspect the affected scene. Invalid sizes are ignored with a message naming the file.

Texture dumps contain game material; do not share them. This site includes no new texture examples or screenshots. Higher resolution changes presentation, not physics. Widescreen camera changes and high-refresh interpolation remain planned.

Source: [README texture workflow](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/README.md#texture-packs). Return to [modders](modders.md).
