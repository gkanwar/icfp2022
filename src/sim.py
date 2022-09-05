### Simulator for the ISL.

import argparse
from PIL import Image
import numpy as np

import lang
import paint

NCHAN = 4

class ExecutionError(Exception):
    def __init__(self, msg, meta):
        self.msg = msg
        self.meta = meta
        super().__init__(self.msg)
    def __str__(self):
        lineno = self.meta["lineno"]
        line = self.meta["line"]
        return f'{self.msg}\nIn line {lineno}:\n{line}'

LINE_CUT_COST = 7
POINT_CUT_COST = 10
COLOR_COST = 5
SWAP_COST = 3
MERGE_COST = 1

def compute_cost(base_cost, size, width, height):
    canvas_size = width * height
    return round(base_cost * canvas_size / size)

def size(block):
    return block.buf.shape[0] * block.buf.shape[1]

def make_filled_block(x, y, ex, ey, color):
    buf = np.zeros((ex-x, ey-y, NCHAN), dtype=np.uint8)
    buf[:] = color
    return Block(x, y, buf)

class Block:
    def __init__(self, x, y, buf):
        self.x = x
        self.y = y
        self.buf = buf
    def __str__(self):
        ex = self.x + self.buf.shape[0]
        ey = self.y + self.buf.shape[1]
        return f'({self.x},{self.y},{ex},{ey})'
    __repr__ = __str__

class State:
    def __init__(self, width, height, blocks):
        self.width = width
        self.height = height
        self.blocks = blocks
        self.gid = len(self.blocks) - 1

    def validate_block(self, block, *, meta):
        if block not in self.blocks:
            raise ExecutionError(f'Invalid block {move.block}', meta)

    def validate_color(self, color):
        if len(color) != NCHAN:
            raise ExecutionError(f'Invalid color {color}', meta)
        if not all(map(lambda x: isinstance(x, int), color)):
            raise ExecutionError(f'Invalid color {color}', meta)
        if not all(map(lambda x: 0 <= x <= 255, color)):
            raise ExecutionError(f'Invalid color {color}', meta)


    def get_next_bid(self):
        self.gid += 1
        return str(self.gid)

    def apply_color_move(self, move):
        self.validate_block(move.block, meta=move.meta)
        self.validate_color(move.color)
        color = np.array(move.color, dtype=np.uint8)
        block = self.blocks[move.block]
        block.buf[:] = color
        return compute_cost(COLOR_COST, size(block), self.width, self.height)

    def apply_swap_move(self, move):
        self.validate_block(move.block1, meta=move.meta)
        self.validate_block(move.block2, meta=move.meta)
        b1 = self.blocks[move.block1]
        b2 = self.blocks[move.block2]
        if b1.buf.shape != b2.buf.shape:
            raise ExecutionError(
                f'Block shape mismatch {b1.buf.shape} vs {b2.buf.shape}',
                move.meta)
        self.blocks[move.block1].buf, self.blocks[move.block2].buf = (
            self.blocks[move.block2].buf, self.blocks[move.block1].buf
        )
        # NOTE: See Discord messages... I don't know why this is size(b1)
        # instead of max(size(b1), size(b2)) like merge.
        return compute_cost(SWAP_COST, size(b1), self.width, self.height)

    def apply_merge_move(self, move):
        self.validate_block(move.block1, meta=move.meta)
        self.validate_block(move.block2, meta=move.meta)
        b1 = self.blocks[move.block1]
        b2 = self.blocks[move.block2]
        cost = compute_cost(MERGE_COST, max(size(b1), size(b2)), self.width, self.height)
        if b1.x != b2.x and b1.y != b2.y:
            raise ExecutionError(f'Block coords do not align', move.meta)
        new_block = None
        if b1.x == b2.x: # vertically stacked
            if b1.buf.shape[0] != b2.buf.shape[0]:
                raise ExecutionError(f'Block shapes do not align', move.meta)
            if b1.y + b1.buf.shape[1] == b2.y:
                b1.buf = np.concatenate((b1.buf, b2.buf), axis=1)
                new_block = b1
            elif b2.y + b2.buf.shape[1] == b1.y:
                b2.buf = np.concatenate((b2.buf, b1.buf), axis=1)
                new_block = b2
            else:
                raise ExecutionError(f'Blocks are not adjacent', move.meta)
        else: # horizontally stacked
            assert b1.y == b2.y
            if b1.buf.shape[1] != b2.buf.shape[1]:
                raise ExecutionError(f'Block shapes do not align', move.meta)
            if b1.x + b1.buf.shape[0] == b2.x:
                b1.buf = np.concatenate((b1.buf, b2.buf), axis=0)
                new_block = b1
            elif b2.x + b2.buf.shape[0] == b1.x:
                b2.buf = np.concatenate((b2.buf, b1.buf), axis=0)
                new_block = b2
            else:
                raise ExecutionError(f'Blocks are not adjacent', move.meta)
        del self.blocks[move.block1]
        del self.blocks[move.block2]
        self.blocks[self.get_next_bid()] = new_block
        return cost

    def apply_line_cut_move(self, move):
        self.validate_block(move.block, meta=move.meta)
        block = self.blocks[move.block]
        ori = move.orientation
        cost = compute_cost(LINE_CUT_COST, size(block), self.width, self.height)
        assert ori in ['x', 'y']
        if ori == 'y' and (move.pos <= block.y or move.pos >= block.y + block.buf.shape[1]):
            raise ExecutionError(
                f'Line cut at {move.pos} out of bounds '
                f'({block.y}, {block.y+block.buf.shape[1]})', move.meta)
        if ori == 'x' and (move.pos <= block.x or move.pos >= block.x + block.buf.shape[0]):
            raise ExecutionError(
                f'Line cut at {move.pos} out of bounds '
                f'({block.x}, {block.x+block.buf.shape[0]})', move.meta)
        if ori == 'y':
            cut_ind = move.pos - block.y
            buf1 = block.buf[:,:cut_ind]
            buf2 = block.buf[:,cut_ind:]
            b1 = Block(block.x, block.y, buf1)
            b2 = Block(block.x, move.pos, buf2)
        elif ori == 'x':
            cut_ind = move.pos - block.x
            buf1 = block.buf[:cut_ind]
            buf2 = block.buf[cut_ind:]
            b1 = Block(block.x, block.y, buf1)
            b2 = Block(move.pos, block.y, buf2)
        else:
            raise RuntimeError()
        del self.blocks[move.block]
        b1_name = move.block + '.0'
        b2_name = move.block + '.1'
        self.blocks[b1_name] = b1
        self.blocks[b2_name] = b2
        return cost

    def apply_point_cut_move(self, move):
        self.validate_block(move.block, meta=move.meta)
        block = self.blocks[move.block]
        cost = compute_cost(POINT_CUT_COST, size(block), self.width, self.height)
        if (move.point[0] <= block.x or move.point[0] >= block.x + block.buf.shape[0] or
            move.point[1] <= block.y or move.point[1] >= block.y + block.buf.shape[1]):
            raise ExecutionError(
                f'Point cut at {move.point} out of bounds '
                f'({block.x}, {block.x+block.buf.shape[0]}) x '
                f'({block.y}, {block.y+block.buf.shape[1]})', move.meta)
        cut_ind_x = move.point[0] - block.x
        cut_ind_y = move.point[1] - block.y
        buf1 = block.buf[:cut_ind_x,:cut_ind_y]
        buf2 = block.buf[cut_ind_x:,:cut_ind_y]
        buf3 = block.buf[cut_ind_x:,cut_ind_y:]
        buf4 = block.buf[:cut_ind_x,cut_ind_y:]
        b1 = Block(block.x, block.y, buf1)
        b2 = Block(move.point[0], block.y, buf2)
        b3 = Block(move.point[0], move.point[1], buf3)
        b4 = Block(block.x, move.point[1], buf4)
        del self.blocks[move.block]
        b1_name = move.block + '.0'
        b2_name = move.block + '.1'
        b3_name = move.block + '.2'
        b4_name = move.block + '.3'
        self.blocks[b1_name] =  b1
        self.blocks[b2_name] =  b2
        self.blocks[b3_name] =  b3
        self.blocks[b4_name] =  b4
        return cost

    def apply(self, move):
        if isinstance(move, lang.ColorMove):
            return self.apply_color_move(move)
        elif isinstance(move, lang.SwapMove):
            return self.apply_swap_move(move)
        elif isinstance(move, lang.MergeMove):
            return self.apply_merge_move(move)
        elif isinstance(move, lang.LineCutMove):
            return self.apply_line_cut_move(move)
        elif isinstance(move, lang.PointCutMove):
            return self.apply_point_cut_move(move)
        else:
            raise NotImplementedError()

    def render(self):
        canvas = np.zeros((self.width, self.height, NCHAN), dtype=np.uint8)
        for block in self.blocks.values():
            x, y = block.x, block.y
            wx, wy = block.buf.shape[:2]
            assert x >= 0 and y >= 0 and x+wx <= self.width and y+wy <= self.height
            canvas[x:x+wx, y:y+wy] = block.buf
        return canvas

def run_program(state, moves):
    tot_cost = 0
    for move in moves:
        cost = state.apply(move)
        tot_cost += cost
    return {
        'output': state.render(),
        'cost': tot_cost
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname', type=str, required=True)
    parser.add_argument('--out_fname', type=str, default='tmp.png')
    parser.add_argument('--ref', type=str, default=None)
    args = parser.parse_args()

    with open(args.fname, 'r') as f:
        moves =  lang.parse_program(f.read())

    # basic starting state
    # TODO: advanced starting states
    state = State(400, 400, {
        '0': make_filled_block(0, 0, 400, 400, (255,255,255,255))
    })

    res = run_program(state, moves)
    paint.save(res['output'], args.out_fname)

    if args.ref is not None:
        ref = paint.load(args.ref)
        diff_cost = round(paint.diff_cost(ref, res['output']))
    else:
        print('WARNING: No ref specified, skipping diff cost')
        diff_cost = 0
    print(f'Execution cost: {res["cost"]}')
    print(f'Diff cost: {diff_cost}')
    print('Total cost:', res['cost'] + diff_cost)

if __name__ == '__main__':
    main()
