# Theme asset sources

The site uses two small graphics decoded from the locally supplied Mario Kart DS
ROM for the requested game theme:

- `mkds-icon.png`: the 32 × 32 cartridge banner icon (Mario in his kart).
- `mkds-checkerboard.png`: the original title screen's 256 × 256 blue checkerboard
  background, decoded from `Scene/Title/title_s_b.NCGR`, `title_s_b.NCLR`, and
  `title_s_bg.NSCR`.

These graphics are Nintendo game artwork, not original artwork of this project.
No third-party copyright license is granted by this repository. The site is an
independent research project and is not affiliated with Nintendo.

The remaining checker patterns, layout, colors, and interface styling are CSS.
No ROM or raw asset archives are included in the repository.

## MKDSrust branding

- `icon.png`: exact copy of the owner's final wheel from `logos/final/icon_236.png`.
- `favicon.png`: 32 × 32 downsample of that wheel.
- `logo.svg`: owner's final wheel embedded as PNG data, paired with the unchanged
  Apex Trace wordmark from `logos/logo_3.svg`. Embedding keeps the logo self-contained
  for the site and README. The original option's wheel is replaced by the final wheel.

These owner-supplied branding assets are separate from the legacy game graphics above.
The current site shell uses the MKDSrust branding, not the legacy game graphics.
