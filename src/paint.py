### Task is to produce commands to paint the canvas to produce the best,
### cheapest match to the target PNG.

import argparse
from PIL import Image
import numpy as np

def load(fname):
    img = Image.open(fname)
    return np.asarray(img.convert("RGBA"))

def solve(img):
    return [] # TODO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True)
    args = parser.parse_args()
    img = load(args.input)
    print(np.all(img[:,:,3] == 255))
    print('\n'.join(map(str, solve(img))))

if __name__ == '__main__': main()
