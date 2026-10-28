from pathlib import Path
from PIL import Image
import base64, re, subprocess
out = Path(__file__).parent
source = Path(r'C:\Users\cam\dev\logos')
im = Image.open(source / 'final/icon_236.png').convert('RGBA')
for size in (256, 64, 32, 16):
    im.resize((size, size), Image.Resampling.LANCZOS).save(out / ('icon.png' if size == 256 else f'icon_{size}.png'))
im.resize((256,256), Image.Resampling.LANCZOS).save(out/'icon.ico', sizes=[(16,16),(32,32),(48,48),(256,256)])
svg = (source/'logo_3.svg').read_text()
data = base64.b64encode((out/'icon.png').read_bytes()).decode()
svg = re.sub(r'<g transform="translate\(16 16\)">.*?</g>', f'<image x="16" y="16" width="128" height="128" href="data:image/png;base64,{data}"/>', svg)
svg = svg.replace('MKDSrust ? Apex Trace', 'MKDSrust').replace('A compact wheel and sweeping drift arcs turn recompilation into forward momentum.', 'The owner\u2019s wheel artwork with the Apex Trace MKDSrust wordmark.')
(out/'logo.svg').write_text(svg, encoding='utf-8')
(out/'logo_light.svg').write_text(svg, encoding='utf-8')
(out/'logo_dark.svg').write_text(svg.replace('fill:#242A30;stroke:#FAF7F0', 'fill:#FAF7F0;stroke:#242A30'), encoding='utf-8')
for name in ('logo', 'logo_dark'):
    subprocess.run([r'C:\Program Files\Inkscape\bin\inkscape.exe', str(out/f'{name}.svg'), '--export-width=1200', f'--export-filename={out/name}.png'], check=True)
