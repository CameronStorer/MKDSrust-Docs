"""Re-key an input script recorded by logical frame (V-blank count) in run A onto run B's logical frames,
aligning by sample index (V-blank IRQs the game took = game frames), so lag frames that exist in only one
run do not shift the inputs against the game.
usage: python rekey.py A_REC B_REC IN_INPUTS OUT_INPUTS"""
import struct, sys, os, bisect

def frames(d):
    b = open(os.path.join(d, 'frames.bin'), 'rb').read()
    n = struct.unpack_from('<I', b, 8)[0]
    size = 16 + 8 * n
    return [struct.unpack_from('<I', b, o)[0] for o in range(12, len(b) - size + 1, size)]

fa, fb = frames(sys.argv[1]), frames(sys.argv[2])
lines = open(sys.argv[3]).read().splitlines()
out = [lines[0]]
moved = 0
for l in lines[1:]:
    f = l.split(',')
    L = int(f[0])
    k = bisect.bisect_left(fa, L)  # first sample at or after L (where the recorder applies it)
    if k < len(fb):
        L2 = fb[k] - (fa[k] - L) if k < len(fa) else L
    else:
        L2 = L + (fb[-1] - fa[min(len(fa), len(fb)) - 1])
    moved += L2 != L
    f[0] = str(L2)
    out.append(','.join(f))
open(sys.argv[4], 'w').write('\n'.join(out) + '\n')
print(f"{len(lines) - 1} rows, {moved} moved")
