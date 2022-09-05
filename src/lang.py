### Parser for the ISL.

class Move:
    meta = None
class ColorMove(Move):
    meta = {'cmd': 'move'}
    def __init__(self, block, color, *, meta):
        self.block = block
        self.color = color
        self.meta['cmd'] = 'move'
        self.meta |= meta
class SwapMove(Move):
    meta = {'cmd': 'swap'}
    def __init__(self, block1, block2, *, meta):
        self.block1 = block1
        self.block2 = block2
        self.meta['cmd'] = 'swap'
        self.meta |= meta
class MergeMove(Move):
    meta = {'cmd': 'merge'}
    def __init__(self, block1, block2, *, meta):
        self.block1 = block1
        self.block2 = block2
        self.meta['cmd'] = 'merge'
        self.meta |= meta
class LineCutMove(Move):
    meta = {'cmd': 'cut'}
    def __init__(self, block, orientation, pos, *, meta):
        self.block = block
        self.orientation = orientation
        self.pos = pos
        self.meta['cmd'] = 'cut (line)'
        self.meta |= meta
class PointCutMove(Move):
    meta = {'cmd': 'cut'}
    def __init__(self, block, point, *, meta):
        self.block = block
        self.point = point
        self.meta |= meta

class ParseError(Exception):
    def __init__(self, msg, meta):
        self.msg = msg
        self.meta = meta
        super().__init__(msg)
    def __str__(self):
        lineno = self.meta["lineno"]
        line = self.meta["line"]
        return f'{self.msg}\nIn line {lineno}:\n{line}'

def parse_num_list(s, meta):
    out = []
    for x in s.replace(' ', '').split(','):
        try:
            out.append(int(x))
        except ValueError:
            raise ParseError(f'Invalid int {x}', meta)
    return out

def parse_block(s, meta):
    if ',' in s:
        raise ParseError(f'Invalid block id {s}', meta)
    return s.strip()

def parse_point(s, meta):
    x,y = parse_num_list(s, meta)
    return (x,y)

def parse_color(s, meta):
    r,g,b,a = parse_num_list(s, meta)
    return (r,g,b,a)

def parse_line_pos(s, meta):
    l = parse_num_list(s, meta)
    if len(l) != 1:
        raise ParseError(f'Line cut pos must be single number, got {s}', meta)
    return l[0]

def parse_orientation(s, meta):
    if s.lower() == 'x':
        return 'x'
    elif s.lower() == 'y':
        return 'y'
    else:
        raise ParseError('Bad orientation', meta)

def parse_line(line, *, meta):
    if line.startswith('#'): return None
    if len(line.strip()) == 0: return None

    # lexing
    head, tail = line.split(' ', 1)
    tail_tokens = tail.strip().split('[')
    assert len(tail_tokens[0]) == 0
    tokens = [head.strip()]
    for tok in tail_tokens[1:]:
        tok = tok.replace(' ', '')
        if not tok.endswith(']'):
            # Actually a lex error...
            raise ParseError('Mismatched brackets', meta)
        tokens.append(tok[:-1])

    # parsing
    assert len(tokens) > 0
    if tokens[0] == 'cut':
        if len(tokens) == 3:
            block = parse_block(tokens[1], meta)
            point = parse_point(tokens[2], meta)
            return PointCutMove(block, point, meta=meta)
        elif len(tokens) == 4:
            block = parse_block(tokens[1], meta)
            orientation = parse_orientation(tokens[2], meta)
            pos = parse_line_pos(tokens[3], meta)
            return LineCutMove(block, orientation, pos, meta=meta)
        else:
            raise ParseError('Invalid cut command', meta)
    elif tokens[0] == 'color':
        if len(tokens) != 3:
            raise ParseError('Invalid color command', meta)
        block = parse_block(tokens[1], meta)
        color = parse_color(tokens[2], meta)
        return ColorMove(block, color, meta=meta)
    elif tokens[0] == 'swap':
        if len(tokens) != 3:
            raise ParseError('Invalid swap command', meta)
        block1 = parse_block(tokens[1], meta)
        block2 = parse_block(tokens[2], meta)
        return SwapMove(block1, block2, meta=meta)
    elif tokens[0] == 'merge':
        if len(tokens) != 3:
            raise ParseError('Invalid merge command', meta)
        block1 = parse_block(tokens[1], meta)
        block2 = parse_block(tokens[2], meta)
        return MergeMove(block1, block2, meta=meta)
    else:
        raise ParseError('Invalid move.', meta)


def parse_lines(lines):
    moves = []
    for i,line in enumerate(lines):
        meta = {'lineno': i+1, 'line': line}
        move = parse_line(line, meta=meta)
        if move is not None:
            moves.append(move)
    return moves


def parse_program(s):
    return parse_lines(s.split('\n'))
