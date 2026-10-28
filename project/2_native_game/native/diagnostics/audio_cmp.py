"""RMS comparison of two MKDS_AUDIO_DUMP captures (raw s16le stereo at 32768 Hz), pure Python.
usage: audio_cmp.py A.raw B.raw [start_s] [len_s]
Aligns B to A (loudness envelopes, then samples, within +-0.25 s) and reports the RMS of each signal, the
RMS of their difference relative to A, and the correlation of the 10 ms loudness envelopes."""
import array
import math
import sys

RATE = 32768


def load(p):
    a = array.array('h')
    with open(p, 'rb') as f:
        a.frombytes(f.read())
    return [(a[i] + a[i + 1]) / 2 for i in range(0, len(a) - 1, 2)]


A, B = load(sys.argv[1]), load(sys.argv[2])
start = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
length = float(sys.argv[4]) if len(sys.argv) > 4 else 10.0
s, n = int(start * RATE), int(length * RATE)
W = 328  # ~10 ms


def env(x, off):
    return [math.sqrt(sum(v * v for v in x[off + i:off + i + W]) / W) for i in range(0, n - W + 1, W)]


def corr(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sxy / (sx * sy) if sx and sy else 0.0


ea = env(A, s)
best, lag = -2, 0
for l in range(-RATE // 4, RATE // 4 + 1, W // 4):
    if s + l < 0 or s + l + n > len(B):
        continue
    c = corr(ea, env(B, s + l))
    if c > best:
        best, lag = c, l
fine, fb = lag, -1e300
seg = A[s:s + n]
for l in range(lag - W // 4, lag + W // 4 + 1):
    if s + l < 0 or s + l + n > len(B):
        continue
    c = sum(a * b for a, b in zip(seg, B[s + l:s + l + n:]))
    if c > fb:
        fb, fine = c, l
segb = B[s + fine:s + fine + n]
rms = lambda x: math.sqrt(sum(v * v for v in x) / len(x))
ra, rb = rms(seg), rms(segb)
rd = rms([a - b for a, b in zip(seg, segb)])
print(f"segment {start}s +{length}s; B aligned by {fine} samples ({fine / RATE * 1000:.1f} ms)")
print(f"RMS A {ra:.1f}  B {rb:.1f}  (B/A {rb / ra if ra else 0:.4f}); difference RMS {rd:.1f} = {rd / ra if ra else 0:.1%} of A")
print(f"10 ms loudness-envelope correlation {corr(env(A, s), env(B, s + fine)):.4f}; sample correlation {corr(seg, segb):.4f}")
