import argparse
import sim
import json
from collections import defaultdict

import paint


# greedily selects swaps repeatedly


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    parser.add_argument('-t', '--initial_state', type=str, required=True)
    args = parser.parse_args()

    # read the initial image as well as the starting state
    with open(args.initial_state) as f:
        data = json.load(f)
    blocks_json = data['blocks']


    # 'bottomLeft': [0, 0], 'topRight': [40, 40]

    blocks_map = {}
    has_been_swapped = defaultdict(bool)
    img = paint.load(args.input)

    for block in blocks_json:
        x, y = block['bottomLeft']
        ex, ey = block['topRight']
        blocks_map[block['blockId']] = sim.make_filled_block(x, y, ex, ey, tuple(block['color']))

    cmds = []
    for block_id in blocks_map.keys():
        cmds.extend(find_best_swap(blocks_map, has_been_swapped, block_id, img))

    print('\n'.join(cmds))
    

def determine_move_cost(width, height):
    return round(3 * (400 * 400) / (width * height))
    


# brute force solution
# just swaps whenever it is better than starting state.
def find_best_swap(blocks_map, has_been_swapped, block_id, img):
    to_swap_block = blocks_map[block_id]
    to_swap_block_width = to_swap_block.buf.shape[0]
    to_swap_block_height = to_swap_block.buf.shape[1]
    to_swap_img_section = img[to_swap_block.x:to_swap_block.x + to_swap_block_width,
                              to_swap_block.y:to_swap_block.y + to_swap_block_height]

    cur_to_cost = paint.diff_cost(to_swap_block.buf, to_swap_img_section)

    move_cost = determine_move_cost(*to_swap_block.buf.shape[:2])
    
    for swap_block_id in blocks_map.keys():
        if has_been_swapped[swap_block_id]:
            continue
        from_swap_block = blocks_map[swap_block_id]
        from_swap_block_width = from_swap_block.buf.shape[0]
        from_swap_block_height = from_swap_block.buf.shape[1]
        from_swap_img_section = img[from_swap_block.x:from_swap_block.x + from_swap_block_width,
                                  from_swap_block.y:from_swap_block.y + from_swap_block_height]

        cur_from_cost = paint.diff_cost(from_swap_block.buf, from_swap_img_section)

        swapped_from_cost = paint.diff_cost(to_swap_block.buf, from_swap_img_section)
        swapped_to_cost = paint.diff_cost(from_swap_block.buf, to_swap_img_section)

        benefit = (cur_to_cost - swapped_to_cost) + (cur_from_cost - swapped_from_cost)

        if benefit > move_cost:
            has_been_swapped[block_id] = True
            has_been_swapped[swap_block_id] = True
            return [f"swap [{block_id}] [{swap_block_id}]"]

    return []
    
    
    

if __name__ == '__main__':
    main()
