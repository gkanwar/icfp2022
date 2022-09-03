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

ALPHA = 0.005
NCHAN = 4

def load(fname):
    img = Image.open(fname)
    return np.asarray(img.convert("RGBA"))

def optimize_color(arr):
    f = lambda x: ALPHA * np.sum(np.sqrt(np.sum((arr - x)**2, axis=-1)))
    x0 = np.array([127]*NCHAN)
    res = sp.optimize.minimize(f, x0, method='CG', tol=0.1)
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
        color_clean = np.clip(np.around(color).astype(int), 0, 255)
        self.fill = Color(*color_clean)

def solve(img):
    NBLOCKS = 16
    assert img.shape[0] % NBLOCKS == 0
    assert img.shape[1] % NBLOCKS == 0
    bx = img.shape[0] // NBLOCKS
    by = img.shape[1] // NBLOCKS
    blocked = img.reshape(NBLOCKS, bx, NBLOCKS, by, NCHAN)
    blocked = np.swapaxes(blocked, 1, 2)
    rects = []
    tot_cost = 0
    for bi in range(NBLOCKS):
        for bj in range(NBLOCKS):
            cij, cost = optimize_color(blocked[bi,bj])
            rects.append(Rect(bi*bx, bj*by, bx, by, cij))
            eprint(rects[-1], cost)
            tot_cost += cost
    eprint(f'solution found with cost {tot_cost}')

    cmds = svgparse.draw_rects(rects)
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
