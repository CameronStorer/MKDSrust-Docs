"""Copy an explicit list of research docs, not the project directory, for publication."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
# (source path in the research workspace, published path (keeps existing page URLs), title, sidebar group)
DOCUMENTS = [
    ('4_docs/BLOCK4_SOURCE_PLAN.md', 'sources/BLOCK4_SOURCE_PLAN.md', 'Block 4 evidence', 'Source reports'),
    ('4_docs/BLOCK5_PLAN.md', 'sources/BLOCK5_PLAN.md', 'Block 5 plan and dated status', 'Source reports'),
    ('4_docs/BLOCK5_CENSUS.md', 'sources/BLOCK5_CENSUS.md', 'Hardware census', 'Source reports'),
    ('4_docs/BLOCK5_DEFAULTS.md', 'sources/BLOCK5_DEFAULTS.md', 'Native defaults proposal', 'Source reports'),
    ('4_docs/masks/native_seed_equalized.md', 'sources/native_seed_equalized.md', 'Earlier seed-pinned proof', 'Source reports'),
    ('launcher/README.md', 'sources/launcher.md', 'Launcher reference', 'Source reports'),
    ('dictionary/README.md', 'sources/dictionary.md', 'Dictionary reference', 'Source reports'),
    ('4_docs/NATIVE_BUILD_STATUS.md', 'docs/NATIVE_BUILD_STATUS.md', 'Native build status', 'Start here'),
    ('4_docs/OBJECTIVES_OWNER_PLAN.md', 'docs/OBJECTIVES_OWNER_PLAN.md', 'Goals and roadmap', 'Start here'),
    ('4_docs/NATIVE_BUILD_BASELINE_AND_CONTRACT.md', 'docs/NATIVE_BUILD_BASELINE_AND_CONTRACT.md', 'Build history and measurements', 'Native build'),
    ('4_docs/ASSET_LAYOUT.md', 'docs/ASSET_LAYOUT.md', 'Asset layout', 'Native build'),
    ('4_docs/GENERATOR_CONTRACT.md', 'docs/GENERATOR_CONTRACT.md', 'Code generator', 'Native build'),
    ('4_docs/RUNTIME_CONTRACT.md', 'docs/RUNTIME_CONTRACT.md', 'Runtime', 'Native build'),
    ('4_docs/FUNCTION_MAP.md', 'docs/FUNCTION_MAP.md', 'Identified functions', 'Function maps'),
    ('4_docs/FUNCTION_TABLE.md', 'docs/FUNCTION_TABLE.md', 'Inventory coverage', 'Function maps'),
    ('4_docs/function_notes.md', 'docs/function_notes.md', 'Function meanings', 'Function maps'),
    ('6_data/analysis/race_logic_map.md', 'analysis/race_logic_map.md', 'Race logic', 'Research'),
    ('6_data/analysis/kart_struct.md', 'analysis/kart_struct.md', 'Kart structure', 'Research'),
    ('6_data/analysis/kart_runtime.md', 'analysis/kart_runtime.md', 'Runtime correlations', 'Research'),
    ('6_data/analysis/kart_runtime_drift.md', 'analysis/kart_runtime_drift.md', 'Drift correlations', 'Research'),
    ('6_data/analysis/state_machines.md', 'analysis/state_machines.md', 'State machines', 'Research'),
    ('6_data/analysis/vm_report.md', 'analysis/vm_report.md', 'VM / dispatcher scan', 'Research'),
    ('6_data/analysis/CODEX_ANIMATION_MAP.md', 'analysis/CODEX_ANIMATION_MAP.md', 'Animation logic', 'Research'),
    ('6_data/analysis/CODEX_PARTICLE_MAP.md', 'analysis/CODEX_PARTICLE_MAP.md', 'Particles and fall contacts', 'Research'),
    ('6_data/analysis/CODEX_NPC_MAP.md', 'analysis/CODEX_NPC_MAP.md', 'NPC and traffic animation', 'Research'),
    ('4_docs/CODEX_NSBCA_HANDOFF.md', 'docs/CODEX_NSBCA_HANDOFF.md', 'Joint-animation decoder', 'Research'),
    ('4_docs/CODEX_NSBTP_HANDOFF.md', 'docs/CODEX_NSBTP_HANDOFF.md', 'Face-pattern decoder', 'Research'),
    ('PROGRESS.md', 'PROGRESS.md', 'Shared progress (hand port)', 'Hand-port archive'),
    ('4_docs/NEXT_GOALS.md', 'docs/NEXT_GOALS.md', 'Hand-port goals', 'Hand-port archive'),
    ('4_docs/ROADMAP.md', 'docs/ROADMAP.md', 'Hand-port roadmap', 'Hand-port archive'),
    ('4_docs/KART_PORT.md', 'docs/KART_PORT.md', 'Kart port findings', 'Hand-port archive'),
    ('4_docs/CODEX_RAINBOW_WORK_LOG.md', 'docs/CODEX_RAINBOW_WORK_LOG.md', 'Rainbow Road movement fidelity', 'Hand-port archive'),
    ('4_docs/CODEX_ROM_BUILD_WORKFLOW.md', 'docs/CODEX_ROM_BUILD_WORKFLOW.md', 'Early ROM build workflow', 'Hand-port archive'),
    ('4_docs/RUST_PROJECT_COMPARISON.md', 'docs/RUST_PROJECT_COMPARISON.md', 'Rust project comparison', 'Hand-port archive'),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT.parents[1])  # website lives in <workspace>/4_docs/website
    args = parser.parse_args()
    source = args.source.resolve()
    target = ROOT / 'content'
    target.mkdir(exist_ok=True)
    manifest = {'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 'documents': []}
    previous = {p['path']: p for p in json.loads((target / 'manifest.json').read_text(encoding='utf-8'))['documents']} if (target / 'manifest.json').exists() else {}
    for src_rel, rel, title, group in DOCUMENTS:
        path = source / src_rel
        if not path.exists() and not rel.startswith('sources/') and (target / rel).exists():
            # Older research files no longer live in the native-only checkout.
            entry = dict(previous[rel])
            entry['group'] = 'Function maps' if group == 'Function maps' else 'Research archive'
            manifest['documents'].append(entry)
            print(f'Retained historical snapshot: {rel} (source absent)')
            continue
        text = path.read_text(encoding='utf-8-sig')
        if not re.match(r'^#\s+\S', text.lstrip()):
            raise ValueError(f'{src_rel}: expected a Markdown title; refusing to sync')
        # Normalize machine-specific paths; never import credentials or arbitrary folders.
        text = re.sub(r'C:[/\\]Users[/\\]camer[/\\]Desktop[/\\]My_NDS_GAME', 'WORKSPACE', text, flags=re.I)
        text = re.sub(r'C:[/\\]Users[/\\][^\s`)"\']+', 'LOCAL_PATH', text, flags=re.I)
        # Public naming: the game is referred to as MKDS.
        text = re.sub(r'Mario\s*Kart\s*DS', 'MKDS', text, flags=re.I)
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')
        manifest['documents'].append({'path': rel, 'title': title, 'group': group if group in ('Function maps', 'Source reports') else 'Research archive', 'modified': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime('%Y-%m-%d')})
    for path in sorted((target / 'guides').glob('*.md')):
        title, group = path.read_text(encoding='utf-8-sig').splitlines()[0:2]
        manifest['documents'].append({'path': path.relative_to(target).as_posix(), 'title': title.removeprefix('# '), 'group': group.removeprefix('<!-- ').removesuffix(' -->'), 'modified': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime('%Y-%m-%d')})
    # Native-only checkouts may not contain the legacy mapping export or figure.
    # Never import new game images: retain the existing reviewed research figure.
    inventory = source / '4_docs/FUNCTION_TABLE.csv'
    if inventory.exists():
        shutil.copyfile(inventory, target / 'functions.csv')
    elif not (target / 'functions.csv').exists():
        raise FileNotFoundError('No source or retained function inventory')
    else:
        print('Retained historical function inventory (source absent)')
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Prepared {len(manifest["documents"])} documentation pages (reviewed reports, retained history and authored guides)')


if __name__ == '__main__':
    main()
