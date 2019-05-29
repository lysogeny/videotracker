"""Various helper functions"""

import os

import cv2

def disconnect(signal):
    """Disconnects the signal, catching any TypeError"""
    try:
        signal.disconnect()
    except TypeError:
        pass

def video_max_frame(filename):
    """For a video file handle, finds out how many frames the video has.

    This works by changing cv2.CAP_PROP_POS_AVI_RATIO to 1, and checking at what
    frame we are.  If your filename does not exist, raises a FileNotFoundError.
    If your filename is not a video, raises a different error.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)
    cap = cv2.VideoCapture(filename)
    test = cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0)
    if not test:
        raise ValueError('File is not a video: `%s`' % filename)
    return int(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
