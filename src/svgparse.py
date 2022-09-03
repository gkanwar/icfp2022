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

def line_to_str(l):
    return f"[{int(l)}]"

def color_to_str(c):
    return f"[{c.red}, {c.green}, {c.blue}, {c.alpha}]"

def merge_str(block_idx1, block_idx2):
    return f"merge [{block_idx1}] [{block_idx2}]"

class MergeToken:
    def __init__(self, x):
        self.x = x
    def __str__(self):
        return f'TOKEN{self.x}'
next_token = MergeToken(0)
def make_merge_token():
    global next_token
    token = next_token
    next_token = MergeToken(token.x+1)
    return token

# performs two point cuts, then one color command and returns everything to starting state.
# returns the commands to extend with and the new block index.
def draw_rect(rect, block_idx, global_idx):
    ret = []
    rect_top_left = (round(rect.x), round(400 - rect.y))
    rect_bottom_right = (
        round(rect.x + rect.width),
        round(400 - (rect.y + rect.height)))

    merge_stack = []
    def safe_cut(pt, bid, kind):
        x,y = pt
        x_edge = x == 0 or x == 400
        y_edge = y == 0 or y == 400
        def replace_bid(tok):
            for m in merge_stack:
                if m[0] == bid:
                    m[0] = tok
                elif m[1] == bid:
                    m[1] = tok
        if x_edge and y_edge:
            return bid
        elif x_edge:
            ret.append(f"cut [{bid}] [y] {line_to_str(y)}")
            tok = make_merge_token()
            merge_stack.append([f"{bid}.0", f"{bid}.1", tok])
            replace_bid(tok)
            return f"{bid}.0" if kind == 'top_left' else f"{bid}.1"
        elif y_edge:
            ret.append(f"cut [{bid}] [x] {link_to_str(x)}")
            tok = make_merge_token()
            merge_stack.append([f"{bid}.0", f"{bid}.1", tok])
            replace_bid(tok)
            return f"{bid}.1" if kind == 'top_left' else f"{bid}.0"
        else:
            ret.append(f"cut [{bid}] {point_to_str(pt)}")
            tok1 = make_merge_token()
            tok2 = make_merge_token()
            tok = make_merge_token()
            merge_stack.append([tok1, tok2, tok])
            merge_stack.append([f"{bid}.0", f"{bid}.1", tok1])
            merge_stack.append([f"{bid}.2", f"{bid}.3", tok2])
            replace_bid(tok)
            return f"{bid}.1" if kind == 'top_left' else f"{bid}.3"

    # two cuts to make the corner of a block
    # ret.append(f"cut [{block_idx}] {point_to_str(rect_top_left)}")
    # ret.append(f"cut [{block_idx}.1] {point_to_str(rect_bottom_right)}")
    block_idx = safe_cut(rect_top_left, block_idx, 'top_left')
    block_idx = safe_cut(rect_bottom_right, block_idx, 'bottom_right')
    # then color the "center" block.
    # ret.append(f"color [{block_idx}.1.3] {color_to_str(rect.fill)}")
    ret.append(f"color [{block_idx}] {color_to_str(rect.fill)}")
    # then return everything to the starting state by merging everything together again.
    # ret.append(merge_str(f"{block_idx}.1.3", f"{block_idx}.1.2"))
    # ret.append(merge_str(f"{block_idx}.1.0", f"{block_idx}.1.1"))
    # ret.append(merge_str(block_idx+1, block_idx+2))
    # ret.append(merge_str(f"{block_idx}.0", block_idx+3))
    # ret.append(merge_str(f"{block_idx}.3", f"{block_idx}.2"))
    # ret.append(merge_str(block_idx+4, block_idx+5))

    tok_dict = dict()
    for merge in reversed(merge_stack):
        A, B, tok = merge
        if isinstance(A, MergeToken):
            A = tok_dict[str(A)]
        if isinstance(B, MergeToken):
            B = tok_dict[str(B)]
        ret.append(merge_str(A, B))
        global_idx += 1
        tok_dict[str(tok)] = global_idx

    return ret, global_idx

    

def main(argv):
    svg_file = argv[0]
    with open(svg_file) as f:
        svg = svgelements.SVG.parse(f)

    rects = flatten(svg)
    # print(rects)


    cmds = []
    if rects[0].width == 400:
        cmds.append(f"color [0] {color_to_str(rects[0].fill)}")
        rects = rects[1:]

    block_idx = 0
    global_idx = 0
    for rect in rects:
        new_cmds, global_idx = draw_rect(rect, block_idx, global_idx)
        block_idx = global_idx
        cmds.extend(new_cmds)
    
    print("\n".join(cmds))



if __name__ == "__main__":
   main(sys.argv[1:])
