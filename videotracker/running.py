"""Various functions for running Qt applications with less issues.

For interrupt handling see: https://coldfix.eu/2016/11/08/pyqt-boilerplate/

"""

import signal

from PyQt5 import QtCore, QtGui, QtWidgets

def setup_interrupt_handling():
    """Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt."""
    signal.signal(signal.SIGINT, _interrupt_handler)
    # Regularly run some (any) python code, so the signal handler gets a
    # chance to be executed:
    safe_timer(50, lambda: None)

def _interrupt_handler(signum, frame):
    """Handle KeyboardInterrupt: quit application."""
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

