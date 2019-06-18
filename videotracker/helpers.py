"""Various helper functions"""

import os

from PyQt5 import QtWidgets, QtCore

import cv2

def disconnect(signal, *args, **kwargs):
    """Disconnects the signal, catching any TypeError"""
    try:
        signal.disconnect(*args, **kwargs)
        return True
    except TypeError:
        pass
    else:
        return False

def video_max_frame(filename: str) -> int:
    """For a video file handle, finds out how many frames the video has.

    This works by changing cv2.CAP_PROP_POS_AVI_RATIO to 1, and checking at what
    frame we are.  If your filename does not exist, raises a FileNotFoundError.
    If your filename is not a video, raises a ValueError.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    cap = cv2.VideoCapture(filename)
    test = cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0)
    if not test:
        raise ValueError('File is not a video: `%s`' % filename)
    value = int(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
    cap.release()
    return value

def change_cursor(value: bool):
    """Changes cursor for the app. When true changes to hourglass, when false to normal"""
    if value:
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
    else:
        QtWidgets.qApp.restoreOverrideCursor()

def get_image(file_handle):
    """Attempts to read an image from file_handle in several ways

    First reads images with cv2.imread. If that fails, tries cv2.VideoCapture.
    raises ValueError if that fails, else returns first image from video or
    just the image.
    """
    if not os.path.exists(file_handle):
        raise FileNotFoundError
    img = cv2.imread(file_handle)
    if img is not None:
        return img
    cap = cv2.VideoCapture(file_handle)
    ok, img = cap.read() # pylint: disable=invalid-name # This name is fine
    cap.release()
    if ok:
        return img
    raise ValueError('File is not readable by OpenCV. Are you sure it contains images?')
