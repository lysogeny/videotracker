"""CLI interface"""

import argparse

# Pylint may not like this, but this is the way it is
# pylint: disable=invalid-name
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input',
                    nargs='?', default=None,
                    help='Open a specific file')
parser.add_argument('-c', '--csv',
                    nargs='?', default=None,
                    help='Write CSV to a specific file')
parser.add_argument('-o', '--output',
                    nargs='?', default=None,
                    help='Write video to a specific file')
parser.add_argument('-m', '--module',
                    nargs='?', default=None,
                    help='Loads a specific module')
