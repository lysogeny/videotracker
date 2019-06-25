"""Entrypoints for the videotracker"""

import sys
import logging

from PyQt5.QtWidgets import QApplication

from . import windows
from . import cli

def gui():
    """GUI entrypoint"""
    parser = cli.parser
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper()))
    app = QApplication(sys.argv)
    cli.setup_interrupt_handling()
    #sys.excepthook = cli.pop_exception
    widget = windows.MainView(csv_file=args.csv, vid_file=args.output,
                              in_file=args.input, debug=args.debug)
    widget.show()
    sys.exit(app.exec_())
