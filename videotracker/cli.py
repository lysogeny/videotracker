"""CLI interface"""

import argparse

class Parser(argparse.ArgumentParser):
    """Argument parser for videotracker"""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.add_argument('-o', '--open',
                          nargs='?', default=None,
                          help='Open a specific file')
        self.add_argument('-c', '--csv',
                          nargs='?', default=None,
                          help='Write CSV to a specific file')
        self.add_argument('-v', '--vid',
                          nargs='?', default=None,
                          help='Write video to a specific file')
        self.add_argument('-m', '--module',
                          nargs='?', default=None,
                          help='Loads a specific module')
