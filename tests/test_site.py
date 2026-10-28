"""Regression checks for audience navigation, Markdown links and read-only sync."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build
import sync


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])


class SiteTests(unittest.TestCase):
    def test_markdown_features_and_stable_anchors(self):
        rendered, toc = build.render_markdown('# Title\n\n## A `code` heading\n\n## A `code` heading\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```rust\nlet a = 1;\n```')
        self.assertIn('id="a-code-heading"', rendered)
        self.assertIn('id="a-code-heading_1"', rendered)
        self.assertIn('<table>', rendered)
        self.assertIn('language-rust', rendered)
        self.assertIn('href="#a-code-heading"', toc)

    def test_generated_audience_links_and_fragments(self):
        manifest = json.loads((ROOT / 'content/manifest.json').read_text(encoding='utf-8'))
        paths = [p['path'] for p in manifest['documents']]
        self.assertEqual(len(paths), len(set(paths)))
        home = (build.OUT / 'index.html').read_text(encoding='utf-8')
        for entry in ('modders', 'pipeline', 'start', 'status', 'glossary', 'faq', 'developer-tools'):
            self.assertIn(f'guides--{entry}.html', home)
        pages = {p: Links(p.read_text(encoding='utf-8')) for p in build.OUT.glob('*.html')}
        for path in sorted(pages):
            parsed = pages[path]
            self.assertEqual(len(parsed.ids), len(set(parsed.ids)), path.name)
            for href in parsed.links:
                if '://' in href or href.startswith('mailto:'):
                    continue
                target, _, fragment = href.partition('#')
                dest = path.parent / target if target else path
                self.assertTrue(dest.is_file(), (path.name, href))
                if fragment:
                    ids = pages[dest].ids
                    self.assertIn(fragment, ids, (path.name, href))
        historical = (build.OUT / 'docs--native_build_status.html').read_text(encoding='utf-8')
        self.assertIn('Historical research snapshot', historical)
        self.assertIn('guides--status.html', historical)

    def test_sync_retains_history_and_does_not_write_source(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            root = Path(temp)
            source = root / 'source'
            target = root / 'site'
            (source / 'dictionary').mkdir(parents=True)
            (target / 'project/launcher').mkdir(parents=True)
            (target / 'content/guides').mkdir(parents=True)
            (target / 'content/docs').mkdir()
            (target / 'project/launcher/README.md').write_text('\ufeff# Launcher\nOriginal notes', encoding='utf-8')
            (target / 'content/docs/old.md').write_text('# History', encoding='utf-8')
            (target / 'content/guides/status.md').write_text('# Status\n<!-- Start here -->\n', encoding='utf-8')
            (target / 'content/functions.csv').write_text('name,status\nold,unknown\n', encoding='utf-8')
            old = {'path': 'docs/old.md', 'title': 'History', 'group': 'Start here', 'modified': '2020-01-01'}
            (target / 'content/manifest.json').write_text(json.dumps({'documents': [old]}), encoding='utf-8')
            (source / 'dictionary/README.md').write_text('# Dictionary\nMain checkout', encoding='utf-8')
            (source / 'launcher').mkdir()
            (source / 'launcher/README.md').write_text('# Stale main copy', encoding='utf-8')
            (target / 'project/4_docs').mkdir()
            (target / 'project/4_docs/report.md').write_text('# Local report\nMoved evidence', encoding='utf-8')
            before_project = {p.relative_to(target / 'project'): p.read_bytes() for p in (target / 'project').rglob('*') if p.is_file()}
            before = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
            docs = [('launcher/README.md', 'sources/launcher.md', 'Launcher', 'Source reports'), ('absent.md', 'docs/old.md', 'History', 'Start here'), ('dictionary/README.md', 'sources/dictionary.md', 'Dictionary', 'Source reports'), ('4_docs/report.md', 'sources/report.md', 'Report', 'Source reports')]
            with patch.object(sync, 'ROOT', target), patch.object(sync, 'DOCUMENTS', docs), patch.object(sys, 'argv', ['sync.py', '--source', str(source)]):
                sync.main()
            result = json.loads((target / 'content/manifest.json').read_text(encoding='utf-8'))
            history = next(p for p in result['documents'] if p['path'] == 'docs/old.md')
            self.assertEqual(history['modified'], '2020-01-01')
            self.assertEqual(history['group'], 'Research archive')
            self.assertEqual(len(result['documents']), 5)
            self.assertEqual((target / 'content/sources/launcher.md').read_text(encoding='utf-8'), '# Launcher\nOriginal notes')
            self.assertEqual((target / 'content/sources/dictionary.md').read_text(encoding='utf-8'), '# Dictionary\nMain checkout')
            after = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            self.assertEqual((target / 'content/sources/report.md').read_text(encoding='utf-8'), '# Local report\nMoved evidence')
            self.assertEqual(before_project, {p.relative_to(target / 'project'): p.read_bytes() for p in (target / 'project').rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
