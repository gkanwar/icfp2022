### Submit file as solution

import api
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fname',  type=str, required=True)
    parser.add_argument('--num', type=int, required=True)
    args = parser.parse_args()
    print(api.submit_file(args.fname, num=args.num))

if __name__ == '__main__': main()
