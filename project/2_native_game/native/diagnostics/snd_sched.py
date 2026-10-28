"""Make a replay schedule (SCHED format for MKDS_SND_REPLAY) from an exact-model MKDS_SND_LOG.
usage: sched.py exact.log out.sched
After Z: B..b = driver loop body (K k = its call k starts), I..E = interrupt handler. Reads (L) go to the
innermost context; reads in a body by another thread (T differs from the thread of the body's first read)
are dropped. An interrupt inside a body becomes `P k bit` (run after the body's call k; before call k when that call
had made no logged read yet)."""
import sys

seen = False
body = None      # [msg, reads, nested]
irq = None       # [bit, reads]
k = since_k = 0
thread = body_thread = None
marks = []
for line in open(sys.argv[1]):
    p = line.split()
    if not p:
        continue
    t = p[0]
    if t == 'Z':
        seen = True
        continue
    if not seen:
        continue
    if t == 'T':
        thread = p[1]
    elif t == 'B':
        body, k, body_thread = ['B', p[1], [], []], 0, None
        marks.append(body)
    elif t == 'K':
        if body is not None:
            k, since_k = int(p[1]), 0
    elif t == 'C':
        # an SND command list delivered in this interrupt; whether the body itself executes it (reads it
        # later) decides whether the interrupt came before or after the body's command execution
        if body is not None and irq is not None:
            body[3][-1].append(int(p[1], 16))
    elif t == 'b':
        body = None
    elif t == 'I':
        irq = [p[1], []]
        if body is not None:
            # an interrupt during call k: replayed after it (before call 1 if it came before any call)
            # one that came before the call made any (logged) read is replayed before that call
            body[3].append([k if since_k else max(k - 1, 0), irq, k])
            if k == 2 and not since_k:
                body[3][-1][0] = 2  # during command execution: after it, unless the body reads its command
        else:
            marks.append(['I', p[1], irq[1], []])
    elif t == 'E':
        irq = None
    elif t == 'L':
        if body is not None and body_thread is None:
            body_thread = thread
        if irq is not None:
            irq[1].append(line)
        elif body is not None and thread == body_thread:
            body[2].append(line)
            since_k += 1
            a = int(p[1], 16)
            for n in body[3]:
                if len(n) > 3 and a in n[3:] and n[0] >= 2:
                    n[0] = 1  # executed by this body's snd_command_execute (call 2): replay before it

with open(sys.argv[2], 'w') as out:
    out.write('SCHED\n')
    for kind, v, reads, nested in marks:
        out.write(f'{kind} {v}\n')
        out.writelines(reads)
        for kk, (bit, r), *_ in nested:
            out.write(f'P {kk} {bit}\n')
            out.writelines(r)
print(len(marks), 'marks,', sum(len(m[3]) for m in marks), 'nested interrupts')
