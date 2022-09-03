### Task is to produce commands to paint the canvas to produce the best,
### cheapest match to the target PNG.

import argparse
from PIL import Image
import numpy as np
import scipy as sp
import scipy.optimize
import sys

import svgparse

def eprint(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def color_to_str(x):
    assert len(x) == 4
    return f"[{x[0]}, {x[1]}, {x[2]}, {x[3]}]"


ALPHA = 0.005
NCHAN = 4
NBLOCKS_LOG2 = 3
NBLOCKS = 2**NBLOCKS_LOG2

def load(fname):
    img = Image.open(fname)
    return np.flip(np.swapaxes(np.asarray(img.convert("RGBA")), 0, 1), axis=1)

def optimize_color(arr):
    f = lambda x: ALPHA * np.sum(np.sqrt(np.sum((arr - x)**2, axis=-1)))
    x0 = np.array([127]*NCHAN)
    res = sp.optimize.minimize(f, x0, method='CG', tol=0.01)
    cost = f(res.x)
    return res.x, cost

class Color:
    def __init__(self, r, g, b, a):
        self.red = r
        self.green = g
        self.blue = b
        self.alpha = a

class Rect:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fill = Color(*color)


def draw_pow2_grid(x, y, wx, wy, color_blocks, *, bid, level):
    N = 2**level
    assert color_blocks.shape == (N, N, NCHAN)
    if level == 0:
        color = color_blocks[0,0]
        return [f"color [{bid}] {color_to_str(color)}"]
    assert wx % 2 == 0 and  wy % 2 == 0
    wx_p = wx // 2
    wy_p = wy // 2
    mx, my = x + wx_p, y + wy_p
    cmds = [f"cut [{bid}] [{mx},{my}]"]
    cmds.extend(draw_pow2_grid(
        x, y, wx_p, wy_p, color_blocks[:N//2, :N//2],
        bid=f"{bid}.0", level=level-1))
    cmds.extend(draw_pow2_grid(
        x+wx_p, y, wx_p, wy_p, color_blocks[N//2:, :N//2],
        bid=f"{bid}.1", level=level-1))
    cmds.extend(draw_pow2_grid(
        x+wx_p, y+wy_p, wx_p, wy_p, color_blocks[N//2:, N//2:],
        bid=f"{bid}.2", level=level-1))
    cmds.extend(draw_pow2_grid(
        x, y+wy_p, wx_p, wy_p, color_blocks[:N//2, N//2:],
        bid=f"{bid}.3", level=level-1))
    return cmds

def solve(img):
    assert img.shape[0] % NBLOCKS == 0
    assert img.shape[1] % NBLOCKS == 0
    bx = img.shape[0] // NBLOCKS
    by = img.shape[1] // NBLOCKS
    blocked = img.reshape(NBLOCKS, bx, NBLOCKS, by, NCHAN)
    blocked = np.swapaxes(blocked, 1, 2)
    rects = []
    color_blocks = []
    tot_cost = 0
    for bi in range(NBLOCKS):
        for bj in range(NBLOCKS):
            cij, cost = optimize_color(blocked[bi,bj])
            cij = np.clip(np.around(cij).astype(int), 0, 255)
            rects.append(Rect(bi*bx, bj*by, bx, by, cij))
            eprint(rects[-1], cost)
            color_blocks.append(cij)
            tot_cost += cost
    eprint(f'solution found with cost {tot_cost}')
    color_blocks = np.stack(color_blocks).reshape(
        (NBLOCKS, NBLOCKS, NCHAN))

    # cmds = svgparse.draw_rects(rects)
    cmds = draw_pow2_grid(0, 0, *img.shape[:2], color_blocks, bid='0', level=NBLOCKS_LOG2)
    return cmds

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    args = parser.parse_args()
    img = load(args.input)
    # print(np.all(img[:,:,3] == 255))
    cmds = solve(img)
    print('\n'.join(cmds))

if __name__ == '__main__': main()
