"""CLI interface"""

import argparse
import signal
import traceback

from PyQt5 import QtCore, QtWidgets

# Pylint may not like this, but this is the way I define my parser.
# Subclassing is not a good idea.
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

def pop_exception(*args, **kwargs):
    """Exception will pop up on screen and printed to stdout"""
    exception = traceback.format_exception(*args, **kwargs)
    errorbox = QtWidgets.QMessageBox()
    errorbox.setText("An unexpected error occured:\n{0}".format(''.join(exception)))
    errorbox.exec_()
    traceback.print_exception(*args, **kwargs)

def setup_interrupt_handling():
    """Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt."""
    signal.signal(signal.SIGINT, _interrupt_handler)
    # Regularly run some (any) python code, so the signal handler gets a
    # chance to be executed:
    safe_timer(50, lambda: None)

def _interrupt_handler(signum, frame):
    """Handle KeyboardInterrupt: quit application."""
    # pylint, I don't need the arguments but I have to have them.
    # pylint: disable=unused-argument
    QtWidgets.qApp.quit()

def safe_timer(timeout, func, *args, **kwargs):
    """
    Create a timer that is safe against garbage collection and overlapping
    calls. See: http://ralsina.me/weblog/posts/BB974.html
    """
    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QtCore.QTimer.singleShot(timeout, timer_event)
    QtCore.QTimer.singleShot(timeout, timer_event)
