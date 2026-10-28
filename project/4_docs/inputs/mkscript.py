"""Build an inputs.csv (logical frame, buttons) from a list of (frame, buttons, hold) presses.
Buttons: A1 B2 Sel4 Start8 Right16 Left32 Up64 Down128 R256 L512."""
import sys
def write(path, presses, drive_from=None, drive_to=None):
    ev={}
    for f,b,h in presses:
        ev[f]=b; ev[f+h]=0
    if drive_from is not None:
        # hold A, weave left/right every 90 frames, use an item (L) every 300
        for f in range(drive_from, drive_to, 30):
            k=(f-drive_from)//30
            b=1 | (16 if k%6==1 else 32 if k%6==4 else 0) | (512 if k%10==5 else 0)
            ev[f]=b
    rows=sorted(ev.items())
    with open(path,'w') as o:
        o.write('frame,buttons,x,y\n1,0,,\n')
        last=0
        for f,b in rows:
            if b!=last: o.write(f'{f},{b},,\n'); last=b
A=1;B=2;DOWN=128;UP=64;RIGHT=16;LEFT=32
base=[(481,A,7),(600,A,8),(720,A,8),(840,A,8),(960,A,8)]
mode=sys.argv[1]; out=sys.argv[2]
if mode=='battle':
    p=base+[(1100,DOWN,8),(1130,DOWN,8),(1160,DOWN,8)]+[(1200+120*k,A,8) for k in range(10)]
    write(out,p,3000,9000)
elif mode=='mission':
    p=base+[(1100,DOWN,8),(1130,DOWN,8),(1160,DOWN,8),(1190,DOWN,8)]+[(1230+120*k,A,8) for k in range(12)]
    write(out,p,1900,4500)
elif mode=='menus':
    p=[(481,A,7),(600,A,8),(720,A,8),(840,A,8),
       (1000,DOWN,8),(1030,DOWN,8),(1060,DOWN,8),(1100,A,8),      # Records
       (1250,DOWN,8),(1300,DOWN,8),(1350,A,8),(1500,B,8),(1600,B,8), # browse, back out
       (1700,DOWN,8),(1730,DOWN,8),(1760,DOWN,8),(1790,RIGHT,8),(1830,A,8), # Options
       (1950,DOWN,8),(2000,DOWN,8),(2050,A,8),(2200,B,8),(2260,B,8),         # an option page, back
       (2250,DOWN,8),(2300,DOWN,8),(2350,A,8),(2500,B,8),(2600,B,8), # another, back to main
       (2700,DOWN,8),(2740,A,8),(2900,B,8)]
    write(out,p)
