#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QApplication

from videotracker import cli, segmentations

def main():
    """A main function"""
    app = QApplication(sys.argv)
    cli.setup_interrupt_handling()
    widget = segmentations.ThresholdSegmentation()
    widget.setWindowTitle('pyqt-stuff')
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
