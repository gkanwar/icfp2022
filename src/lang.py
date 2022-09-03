### Parser for the ISL.

class Move:
    kind = None
class ColorMove(Move):
    def __init__(self, block, color):
        self.block = block
        self.color = color
class SwapMove(Move):
    def __init__(self, block1, block2):
        self.block1 = block1
        self.block2 = block2
class MergeMove(Move):
    def __init__(self, block1, block2):
        self.block1 = block1
        self.block2 = block2
class LineCutMove(Move):
    def __init__(self, block, orientation, pos):
        self.block = block
        self.orientation = orientation
        self.pos = pos
class PointCutMove(Move):
    def __init__(self, block, point):
        self.block = block
        self.point = point

class ParseError(Exception):
    def __init__(self, message):
        super().__init__(message)

def parse_num_list(s):
    if s[0] != '[':
        raise ParseError('bad list')
    if s[-1] != ']':
        raise ParseError('bad list')
    return list(map(int, s[1:-1].replace(' ', '').split(',')))

def parse_block(s):
    l = parse_num_list(s)
    if len(l) != 1:
        raise ParseError(f'Invalid block id {s}')
    i = l[0]
    return tuple(map(int, i.split('.')))

def parse_point(s):
    x,y = parse_num_list(s)
    return (x,y)

def parse_color(s):
    r,g,b,a = parse_num_list(s)
    return (r,g,b,a)

def parse_line_pos(s):
    l = parse_num_list(s)
    if len(l) != 1:
        raise ParseError(f'Invalid block id {s}')
    i = l[0]
    return tuple(map(int, i.split('.')))

def parse_orientation(s):
    if s.lower() == 'x':
        return 'x'
    elif s.lower() == 'y':
        return 'y'
    else:
        raise ParseError('Bad orientation')

def parse_line(line):
    if line.startswith('#'): return None
    if len(line.strip()) == 0: return None
    tokens = line.strip().split()
    assert len(tokens) > 0
    if tokens[0] == 'cut':
        if len(tokens) == 3:
            block = parse_block(tokens[1])
            point = parse_point(tokens[2])
            return PointCutMove(block, point)
        elif len(tokens) == 4:
            block = parse_block(tokens[1])
            orientation = parse_orientation(tokens[2])
            pos = parse_line_pos(tokens[3])
            return LineCutMove(block, orientation, pos)
        else:
            raise ParseError('Invalid cut command')
    elif tokens[0] == 'color':
        if len(tokens) != 3:
            raise ParseError('Invalid color command')
        block = parse_block(tokens[1])
        color = parse_color(tokens[2])
        return ColorMove(block, color)
    elif tokens[0] == 'swap':
        if len(tokens) != 3:
            raise ParseError('Invalid swap command')
        block1 = parse_block(tokens[1])
        block2 = parse_block(tokens[2])
        return SwapMove(block1, block2)
    elif tokens[0] == 'merge':
        if len(tokens) != 3:
            raise ParseError('Invalid merge command')
        block1 = parse_block(tokens[1])
        block2 = parse_block(tokens[2])
        return MergeMove(block1, block2)
    else:
        raise ParseError('Invalid move.')

def parse_program(s):
    moves = list(map(parse_line, s.split('\n')))
    return moves
