"""Entrypoints for the videotracker"""

import sys

from PyQt5.QtWidgets import QApplication

from . import widgets
from . import cli

def gui():
    """GUI entrypoint"""
    parser = cli.parser
    args = parser.parse_args()
    app = QApplication(sys.argv)
    cli.setup_interrupt_handling()
    sys.excepthook = cli.pop_exception
    widget = widgets.MainView(csv=args.csv, vid=args.output, in_vid=args.input)
    widget.show()
    sys.exit(app.exec_())
