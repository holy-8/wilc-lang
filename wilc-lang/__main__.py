import argparse
from pathlib import Path
from timeit import timeit
from .interpreter import execute_source


parser = argparse.ArgumentParser(description='Executes a .wilc script')
parser.add_argument('path', help='Path to a file that will get executed')
parser.add_argument('-t', '--timeit', action='store_true')
args = parser.parse_args()


path = Path(args.path)
libs_path = Path(__file__).parent / Path('libs')


exec_time = timeit(lambda: execute_source(path, libs_path), number=1)
if args.timeit:
    print(f'[Finished in {exec_time:.4f}s.]')
