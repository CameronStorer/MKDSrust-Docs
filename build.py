"""Build the public research site from reviewed documentation snapshots."""
from pathlib import Path
from collections import Counter
import csv
import html
import hashlib
import json
import re
import shutil
from urllib.parse import unquote, urlsplit
from markdown_it import MarkdownIt
import unicodedata

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '_site'


def slug(path):
    return path.replace('/', '--').removesuffix('.md').lower() + '.html'


def frame(title, body, active=''):
    versions = {name: hashlib.sha256((ROOT / 'assets' / name).read_bytes()).hexdigest()[:10]
                for name in ('style.css', 'theme.css', 'site.js')}
    manifest = json.loads((ROOT / 'content/manifest.json').read_text(encoding='utf-8'))
    links = []
    # Audience routes first; historical material remains available at stable URLs.
    for group, open_default in (('Start here', True), ('Modders', True),
                                ('Researchers', False), ('For everyone', False),
                                ('Source reports', False), ('Function maps', False),
                                ('Research archive', False)):
        entries = [p for p in manifest['documents'] if p['group'] == group]
        if not entries:
            continue
        is_open = open_default or any(active == p['path'] for p in entries)
        links.append(f'<details class="nav-group"{" open" if is_open else ""}><summary class="nav-label">{group}</summary>')
        for p in entries:
            selected = ' class="selected" aria-current="page"' if active == p['path'] else ''
            links.append(f'<a href="{slug(p["path"])}"{selected}>{html.escape(p["title"])}</a>')
        links.append('</details>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Driftlift</title><meta name="description" content="Driftlift documentation: build and mod your own copy, study static recompilation, and follow project progress.">

<link rel="stylesheet" href="assets/style.css?v={versions['style.css']}"><link rel="stylesheet" href="assets/theme.css?v={versions['theme.css']}"><script src="assets/site.js?v={versions['site.js']}" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html"><span class="brand-name">Driftlift<b>RESEARCH &amp; NATIVE RECOMPILATION</b></span></a>
<nav aria-label="Primary"><a href="index.html">Overview</a><a href="guides--status.html">Project status</a><a href="functions.html">Function explorer</a>
<a href="https://github.com/CameronStorer/MKDS-Native-Builder/tree/block4">Build it yourself ↗</a><a href="https://github.com/CameronStorer/mkds-decomp-docs">GitHub ↗</a></nav>
<button id="menu-toggle" aria-label="Toggle documentation navigation" aria-expanded="false">☰</button></header>
<div class="layout"><aside id="sidebar"><a class="explorer-link" href="functions.html">⌕ Explore functions</a>{''.join(links)}
<div class="snapshot">Documentation snapshot<br><strong>{html.escape(manifest['updated'])}</strong></div></aside>
<main id="main">{body}<footer>Independent research by Cameron Storer. Documentation of a work in progress.
<br>Not affiliated with Nintendo. MKDS and associated names belong to their respective owners.
</footer></main></div></body></html>'''


def rewrite_links(rendered, source, documents):
    def replace(m):
        href = html.unescape(m.group(1))
        text = m.group(2)
        parts = urlsplit(href)
        if parts.scheme in ('https', 'http', 'mailto') or href.startswith('#'):
            return m.group(0)
        target = (ROOT / 'content' / Path(source).parent / unquote(parts.path)).resolve()
        try:
            rel = target.relative_to((ROOT / 'content').resolve()).as_posix()
        except ValueError:
            rel = ''
        if rel in documents:
            fragment = ('#' + parts.fragment) if parts.fragment and not re.fullmatch(r'L\d+', parts.fragment) else ''
            return f'<a href="{slug(rel)}{fragment}">{text}</a>'
        if rel == 'docs/FUNCTION_TABLE.csv':
            return f'<a href="functions.html">{text}</a>'
        return f'<span class="local-reference" title="Reference to a file in the local research workspace">{text}</span>'
    return re.sub(r'<a href="([^"]+)">(.*?)</a>', replace, rendered, flags=re.S)


def render_markdown(source):
    """Render reviewed CommonMark, tables and fenced code with stable heading links."""
    md = MarkdownIt('commonmark', {'html': True}).enable('table')
    tokens = md.parse(source)
    used = set()
    headings = []
    for index, token in enumerate(tokens):
        if token.type != 'heading_open':
            continue
        inline = tokens[index + 1]
        label = ''.join(t.content for t in (inline.children or []) if t.type in ('text', 'code_inline'))
        anchor = unicodedata.normalize('NFKD', label).encode('ascii', 'ignore').decode().lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[-\s]+', '-', anchor).strip('-')
        candidate = anchor
        suffix = 1
        while candidate in used:
            candidate = f'{anchor}_{suffix}'
            suffix += 1
        used.add(candidate)
        token.attrSet('id', candidate)
        if token.tag in ('h2', 'h3'):
            headings.append(f'<li><a href="#{candidate}">{html.escape(label)}</a></li>')
    toc = '<ul>' + ''.join(headings) + '</ul>' if headings else ''
    return md.renderer.render(tokens, md.options, {}), toc


def build():
    OUT.mkdir(exist_ok=True)
    (OUT / 'assets').mkdir(exist_ok=True)
    for p in (ROOT / 'assets').iterdir():
        if p.is_file() and p.suffix != '.md':
            shutil.copyfile(p, OUT / 'assets' / p.name)
    shutil.copyfile(ROOT / 'content/docs/figure8_simulation.png', OUT / 'assets/figure8_simulation.png')
    manifest = json.loads((ROOT / 'content/manifest.json').read_text(encoding='utf-8'))
    documents = {p['path'] for p in manifest['documents']}
    for p in manifest['documents']:
        source = (ROOT / 'content' / p['path']).read_text(encoding='utf-8')
        # Reviewed prose must not introduce executable markup into the public site.
        if re.search(r'<\s*(script|iframe|object|embed|style)\b|\bon\w+\s*=', source, re.I):
            raise ValueError(f'Unreviewed active markup: {p["path"]}')
        rendered, page_toc = render_markdown(source)
        rendered = rewrite_links(rendered, p['path'], documents)
        rendered = rendered.replace('src="figure8_simulation.png"', 'src="assets/figure8_simulation.png"')
        rendered = rendered.replace('<table>', '<div class="table-scroll"><table>')
        rendered = rendered.replace('</table>', '</table></div>')
        toc = f'<details class="page-toc"><summary>On this page</summary>{page_toc}</details>' if page_toc else ''
        archive_note = '<div class="notice">Historical research snapshot. For current Driftlift progress, read <a href="guides--status.html">Project status</a>.</div>' if p['group'] == 'Research archive' else ''
        if p['group'] == 'Source reports':
            archive_note = '<div class="notice">Dated technical evidence, including planned work. Read <a href="guides--status.html">Project status</a> for the current summary.</div>'
        elif p['group'] == 'Function maps':
            archive_note = '<div class="notice">Historical mapping inventory. These classifications are distinct from current whole-program source coverage. See <a href="guides--status.html">Project status</a>.</div>'
        body = f'{archive_note}<div class="eyebrow">{html.escape(p["group"])}</div><div class="source-note">Source: <code>{html.escape(p["path"])}</code> · Updated {html.escape(p["modified"])}</div>{toc}<article class="prose">{rendered}</article>'
        (OUT / slug(p['path'])).write_text(frame(p['title'], body, p['path']), encoding='utf-8')
    with (ROOT / 'content/functions.csv').open(encoding='utf-8-sig', newline='') as f:
        functions = list(csv.DictReader(f))
    fields = ['name', 'segment', 'ea', 'size', 'status', 'area', 'meaning', 'callers', 'callees', 'our_code']
    data = [{key: row.get(key, '') for key in fields} for row in functions]
    (OUT / 'assets/functions.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    counts = Counter(p['status'] for p in functions)
    counts['annotated'] = counts['known'] + counts['described']
    cards = ''.join(f'<div class="stat"><strong>{counts[s]:,}</strong><span>{label}</span></div>' for s, label in [('annotated', 'Recorded meanings'), ('inferred', 'Inferred areas'), ('sdk', 'SDK classifications'), ('unknown', 'Still unknown')])
    overview = f'''<section class="title-screen" aria-label="Driftlift introduction"><div class="title-screen-copy"><div class="eyebrow">Driftlift / Lift the code. Keep the drift.</div>
<h1>Your game.<br><span class="muted">A new way to understand it.</span></h1>
<p class="lead">Turn your own lawful MKDS cartridge dump into a native game and a Rust source workspace. Explore how it works and how the research is checked. No ROM or game download is supplied.</p>
<div class="hero-actions"><a class="button" href="guides--status.html">Project status</a><a class="text-link" href="guides--start.html">What is Driftlift?</a></div></div></section>
<section class="section"><h2>Choose your path</h2><div class="feature-grid">
<a class="feature" href="guides--modders.html"><span class="feature-number">MODDERS</span><h3>Build and change your copy</h3><p>Graphical launcher, source navigation, dictionary, textures, native switches and verification.</p></a>
<a class="feature" href="guides--pipeline.html"><span class="feature-number">RESEARCHERS</span><h3>Study the method</h3><p>Instruction lifting, IR, raised code, flag liveness, type inference and hardware replacement.</p></a>
<a class="feature" href="guides--start.html"><span class="feature-number">GENERAL READERS</span><h3>Follow the story</h3><p>What recompilation means, why Driftlift exists, the block-by-block journey and what comes next.</p></a>
</div></section>
<section class="section"><h2>Current progress</h2><p>All <strong>12,736 functions</strong> have raised output. Opt-in native services now include CPU-less ARM7 sound execution; the latest budget-free acceptance measurement uses about <strong>28% less CPU per frame</strong>. Native defaults, save files, graphics fixes and readability polish remain work in progress.</p><p>These are dated measurements, not universal compatibility claims. <a href="guides--status.html">Read current status and limits</a>.</p></section>
<section class="section"><h2>Evidence you can inspect</h2><p>The exact reference race is bit-identical after source transformations. Native race comparisons require pinned randomness, documented masks and loading offsets; menus and battle retain differences.</p><a href="guides--verify.html">How verification works</a> · <a href="guides--hardware.html">Native hardware research</a> · <a href="guides--journey.html">Timeline</a></section>
<section class="stats" aria-label="Research inventory classifications">{cards}</section>
<p class="caption">Historical mapping inventory, distinct from the 12,736-function whole-program raised-code count. Classifications describe annotation evidence, not game completion or universal verification. <a href="functions.html">Search {len(functions):,} records</a>.</p>
<p><a href="guides--glossary.html">Glossary</a> · <a href="guides--faq.html">FAQ</a></p>
<div class="notice">Use your own lawful dump. Keep ROM-derived source, assets and built games private. Independent of Nintendo. <a href="guides--start.html">Project and distribution boundaries</a>.</div>'''
    (OUT / 'index.html').write_text(frame('Overview', overview), encoding='utf-8')
    explorer = '''<div class="eyebrow">Code inventory / Search & inspect</div><h1>Function explorer</h1>
<p class="lead">Find a routine by address, meaning, subsystem or Rust counterpart. Click a column heading to sort; click it again to reverse. Scroll to load 200 more rows.</p>
<div class="explorer-controls"><label class="search-label">Search functions<input id="function-search" type="search" placeholder="Try sub_2087B78, steering, animation…" autocomplete="off"></label>
<label>Status<select id="status-filter"><option value="">All statuses</option><option>known</option><option>described</option><option>inferred</option><option>sdk</option><option>unknown</option></select></label>
<label>Area<select id="area-filter"><option value="">All areas</option></select></label></div>
<p class="caption">Known = a reviewed annotation; described = an unverified sweep annotation; inferred = a candidate area; SDK = a library classification; unknown = unmapped. None alone proves frame-exact behavior.</p>
<div id="function-count" role="status" aria-live="polite">Loading function inventory…</div>
<div class="table-scroll"><table class="function-table"><thead><tr>
<th scope="col" aria-sort="none"><button class="column-sort" data-sort="name" data-label="function">Function <span class="sort-indicator" aria-hidden="true">↕</span></button></th>
<th scope="col" aria-sort="none"><button class="column-sort" data-sort="ea" data-label="address">Address / segment <span class="sort-indicator" aria-hidden="true">↕</span></button></th>
<th scope="col" aria-sort="none"><button class="column-sort" data-sort="status" data-label="status">Status <span class="sort-indicator" aria-hidden="true">↕</span></button></th>
<th scope="col" aria-sort="none"><button class="column-sort" data-sort="area" data-label="area">Area <span class="sort-indicator" aria-hidden="true">↕</span></button></th>
<th scope="col" aria-sort="none"><button class="column-sort" data-sort="meaning" data-label="meaning">Meaning <span class="sort-indicator" aria-hidden="true">↕</span></button></th>
</tr></thead><tbody id="function-rows"></tbody></table></div>
<div id="scroll-sentinel" class="load-more-panel"><p id="load-status">Loading function inventory…</p><button id="load-more" class="button" hidden>Load 200 more functions ↓</button></div>
<dialog id="function-detail"><button id="close-detail" class="dialog-close" aria-label="Close function detail">×</button><div id="detail-body"></div></dialog>
<noscript><p>The interactive explorer needs JavaScript. <a href="docs--function_map.html">Read the function map</a> instead.</p></noscript>'''
    (OUT / 'functions.html').write_text(frame('Function explorer', explorer), encoding='utf-8')
    (OUT / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Built {len(documents)} documentation pages and {len(functions):,} function records')


if __name__ == '__main__':
    build()
