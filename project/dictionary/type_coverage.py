"""Type coverage of generated T1 source (mkds_gen output dir): accessor sites, typed arguments,
renamed registers, named-global notes, and the memory accesses still printed as raw helpers.

    python dictionary/type_coverage.py <gen dir>
"""
import glob, os, re, sys

def main(gen):
    mods = set(re.findall(r'^pub mod (\w+) \{', open(os.path.join(gen, 'layout', 'src', 'lib.rs')).read(), re.M))
    acc_re = re.compile(r'\b(\w+)::(\w+)\(m, ')
    raw_re = re.compile(r'\bR::(ldr|ld32|ld16s|ld16|ld8s|ld8|st8|st16|st32)\(m, ')
    glob_re = re.compile(r'0x[0-9A-F]+(?:u32)?\)?[^/]*; // &?[A-Za-z_]\w*$')
    n = dict(t1=0, sites=0, raw=0, args=0, renamed=0, gnotes=0)
    for p in sorted(glob.glob(os.path.join(gen, 'part_*', 'src', 'lib.rs'))):
        in_t1 = False
        prev = ''
        for line in open(p, encoding='utf-8'):
            if line.startswith('/// Arguments:'):
                n['args'] += 1
            if line.startswith('pub fn '):
                in_t1 = None  # decided by the next lines
                continue
            if in_t1 is None:
                if 'R::t1_enabled(' in line:
                    in_t1 = True
                    n['t1'] += 1
                elif not line.lstrip().startswith('#[allow') and 'use recomp::' not in line:
                    in_t1 = False
                continue
            if not in_t1:
                continue
            if line.startswith('}'):
                in_t1 = False
                continue
            if line.startswith('    let (mut ') and '= (c.r[' in line:
                names = re.findall(r'mut (\w+)', line.split('=')[0])
                if any(not re.fullmatch(r'r\d+|sp|lr', x) for x in names):
                    n['renamed'] += 1
            for m_, _ in acc_re.findall(line):
                if m_ in mods:
                    n['sites'] += 1
            n['raw'] += len(raw_re.findall(line))
            if 'reload!()' not in line and glob_re.search(line.rstrip()):
                n['gnotes'] += 1
    tot = n['sites'] + n['raw']
    print(f"T1 functions: {n['t1']}")
    print(f"accessor sites: {n['sites']}  raw accesses: {n['raw']}  ({100.0*n['sites']/max(tot,1):.1f}% of memory accesses named)")
    print(f"functions listing typed arguments: {n['args']}")
    print(f"functions renaming registers: {n['renamed']}")
    print(f"named-global notes: {n['gnotes']}")

if __name__ == '__main__':
    main(sys.argv[1])
