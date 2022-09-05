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
NBLOCKS = 0
# NBLOCKS_LOG2 = 4
# NBLOCKS = 2**NBLOCKS_LOG2
# NBLOCKS = 16

def load(fname):
    img = Image.open(fname)
    return np.flip(np.swapaxes(np.asarray(img.convert("RGBA")), 0, 1), axis=1)

def save(arr, fname):
    img = Image.fromarray(np.swapaxes(np.flip(arr, axis=1), 0, 1), mode='RGBA')
    img.save(fname)

def optimize_color(arr):
    f = lambda x: ALPHA * np.sum(np.sqrt(np.sum((arr - x)**2, axis=-1)))
    x0 = np.array([127.0]*NCHAN)
    res = sp.optimize.minimize(f, x0, method='CG', tol=0.01)
    cost = f(res.x)
    return res.x, cost

def diff_cost(arr1, arr2):
    arr1 = arr1.astype(int)
    arr2 = arr2.astype(int)
    return ALPHA * np.sum(np.sqrt(np.sum((arr1 - arr2)**2, axis=-1)))

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

def cheap_grid(x, y, bx, by, color_blocks, *, bid, gid, ori, bleed):
    Nx = color_blocks.shape[0]
    Ny = color_blocks.shape[1]
    assert color_blocks.shape[2] == NCHAN and len(color_blocks.shape) == 3
    if Nx == 0 or Ny == 0: return []

    cmds = []
    c00 = color_blocks[0,0]
    cmds.append(f'color [{bid}] {color_to_str(c00)}')
    if ori.startswith('vert'):
        NA, NB = Nx, Ny
        oA, oB = 'x', 'y'
        bA, bB = bx, by
        a, b = x, y
        if ori.endswith('A'):
            next_coord = (x, y+by)
            next_b = y + by
            next_slice = (slice(None), slice(1, None))
            make_ind = lambda i: (i,0)
        else:
            assert ori.endswith('B')
            next_coord = (x, y-by)
            next_b = y - by
            next_slice = (slice(None), slice(0, -1))
            make_ind = lambda i: (i,-1)
    else:
        assert ori.startswith('horiz')
        NA, NB = Ny, Nx
        oA, oB = 'y', 'x'
        bA, bB = by, bx
        a, b = y, x
        if ori.endswith('A'):
            next_coord = (x+bx, y)
            next_b = x + bx
            next_slice = (slice(1, None), slice(None))
            make_ind = lambda i: (0,i)
        else:
            assert ori.endswith('B')
            next_coord = (x-bx, y)
            next_b = x - bx
            next_slice = (slice(0, -1), slice(None))
            make_ind = lambda i: (-1,i)
    if ori.endswith('A'):
        next_side = '1'
    else:
        next_side = '0'
    for i in range(1, NA-bleed[0]):
        cmds.append(f'cut [{bid}] [{oA}] [{i*bA}]')
        ci0 = color_blocks[make_ind(i)]
        cmds.append(f'color [{bid}.1] {color_to_str(ci0)}')
        cmds.append(f'merge [{bid}.0] [{bid}.1]')
        bid = str(gid+1)
        gid += 1
    if NB > 1+bleed[1]:
        cmds.append(f'cut [{bid}] [{oB}] [{next_b}]')
        bid = f'{bid}.{next_side}'
        cmds.extend(cheap_grid(
            *next_coord, bx, by, color_blocks[next_slice], bid=bid, gid=gid, ori=ori, bleed=bleed))
    # elif ori == 'horiz':
    #     for i in range(1, Ny):
    #         cmds.append(f'cut [{bid}] [y] [{i*by}]')
    #         ci0 = color_blocks[0,i]
    #         cmds.append(f'color [{bid}.1] {color_to_str(ci0)}')
    #         cmds.append(f'merge [{bid}.0] [{bid}.1]')
    #         bid = str(gid+1)
    #         gid += 1
    #     if Nx > 1+bleed:
    #         cmds.append(f'cut [{bid}] [x] [{x+bx}]')
    #         bid = f'{bid}.1'
    #         cmds.extend(cheap_grid(
    #             x+bx, y, bx, by, color_blocks[1:,:], bid=bid, gid=gid, ori=ori, bleed=bleed))
    # else:
    #     raise RuntimeError()
    return cmds
            
def solve(img, orientation, bleed):
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
            cij, cost = optimize_color(blocked[bi,bj].astype(np.float64))
            cij = np.clip(np.around(cij).astype(int), 0, 255)
            rects.append(Rect(bi*bx, bj*by, bx, by, cij))
            # eprint(rects[-1], cost)
            color_blocks.append(cij)
            tot_cost += cost
    eprint(f'solution found with cost {tot_cost}')
    color_blocks = np.stack(color_blocks).reshape(
        (NBLOCKS, NBLOCKS, NCHAN))

    # cmds = svgparse.draw_rects(rects)
    # cmds = draw_pow2_grid(0, 0, *img.shape[:2], color_blocks, bid='0', level=NBLOCKS_LOG2)
    x0 = 0
    y0 = 0
    if orientation == 'vertB':
        y0 = img.shape[1]
    if orientation == 'horizB':
        x0 = img.shape[0]
    cmds = cheap_grid(
        x0, y0, bx, by, color_blocks, bid='0', gid=0, ori=orientation,
        bleed=bleed)
    return cmds

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-N', '--n_blocks', type=int, default=16)
    parser.add_argument('-O', '--orientation', type=str, default='vertA')
    parser.add_argument('--bleed_A', type=int, default=0, help='bleed A pixels per raster row')
    parser.add_argument('--bleed_B', type=int, default=0, help='bleed the last B raster rows')
    args = parser.parse_args()
    global NBLOCKS
    NBLOCKS = args.n_blocks
    img = load(args.input)
    # print(np.all(img[:,:,3] == 255))
    cmds = solve(img, args.orientation, (args.bleed_A, args.bleed_B))
    print('\n'.join(cmds))

if __name__ == '__main__': main()
