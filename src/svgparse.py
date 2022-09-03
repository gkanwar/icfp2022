# this current setup takes in an svg that can only contain Rects as drawable objects and turns them into
# ton of (inefficient) ISL commands for ICFP 2022.

import sys
import svgelements

# Given a svg tree, returns a list of rectanges from that svg tree
def flatten(svg) -> list:
    ret = []
    for ele in svg:
        if isinstance(ele, list):
            ret.extend(flatten(ele))
        elif isinstance(ele, svgelements.Rect):
            ret.append(ele)
    return ret

def point_to_str(pt):
    return f"[{int(pt[0])}, {int(pt[1])}]"

def color_to_str(c):
    return f"[{c.red}, {c.green}, {c.blue}, {c.alpha}]"

def merge_str(block_idx1, block_idx2):
    return f"merge [{block_idx1}] [{block_idx2}]"


# performs two point cuts, then one color command and returns everything to starting state.
# returns the commands to extend with and the new block index.
def draw_rect(rect, block_idx):
    ret = []
    rect_top_left = (rect.x, 400 - rect.y)
    rect_bottom_right = (rect.x + rect.width, 400 - (rect.y + rect.height))
    # two cuts to make the corner of a block
    ret.append(f"cut [{block_idx}] {point_to_str(rect_top_left)}")
    ret.append(f"cut [{block_idx}.1] {point_to_str(rect_bottom_right)}")
    # then color the "center" block.
    ret.append(f"color [{block_idx}.1.3] {color_to_str(rect.fill)}")
    # then return everything to the starting state by merging everything together again.
    ret.append(merge_str(f"{block_idx}.1.3", f"{block_idx}.1.2"))
    ret.append(merge_str(f"{block_idx}.1.0", f"{block_idx}.1.1"))
    ret.append(merge_str(block_idx+1, block_idx+2))
    ret.append(merge_str(f"{block_idx}.0", block_idx+3))
    ret.append(merge_str(f"{block_idx}.3", f"{block_idx}.2"))
    ret.append(merge_str(block_idx+4, block_idx+5))

    return ret, block_idx+6

    

def main(argv):
    svg_file = argv[0]
    with open(svg_file) as f:
        svg = svgelements.SVG.parse(f)

    rects = flatten(svg)
    print(rects)


    cmds = []
    if rects[0].width == 400:
        cmds.append(f"color [0] {color_to_str(rects[0].fill)}")
        rects = rects[1:]

    block_idx = 0
    for rect in rects:
        new_cmds, block_idx = draw_rect(rect, block_idx)
        cmds.extend(new_cmds)
    
    print("\n".join(cmds))



if __name__ == "__main__":
   main(sys.argv[1:])
