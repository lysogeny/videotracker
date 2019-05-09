"""OpenCV video file abstractions.

A Video object abstracts the videofile.
"""

from typing import Tuple

import cv2

class Video:
    """Video object.

    Abstraction for video files.
    This has a couple of usages.

    1) Use as an iterator:
        It is possible to use Video as an iterator. This way it will return each
        frame in the video until running out of frames.

    2) Use as not an iterator:
        It is possible to use this like any other object.  This is more useful
        for addressing individual frames instead of getting them in order.
        See methods `frame` and `grab` for more.
    """
    def __init__(self, file_name: str):
        super().__init__()
        self.stopped = False
        self._frame = None
        self._new = True
        self.file_name = file_name
        self.capture = cv2.VideoCapture(self.file_name)

    @property
    def position(self) -> int:
        """The position in the video"""
        return self.capture.get(cv2.CAP_PROP_POS_FRAMES)
    @position.setter
    def position(self, position: int):
        """Sets the new frame index"""
        if self.position != position:
            self._new = True
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, position)

    @property
    def time(self) -> float:
        """The time at which the video is currently in milliseconds"""
        return self.capture.get(cv2.CAP_PROP_POS_MSEC)
    @time.setter
    def time(self, time: float):
        """Sets the new time index"""
        self.capture.set(cv2.CAP_PROP_POS_MSEC, time)

    @property
    def framerate(self) -> float:
        """Framerate of the video"""
        self.framerate = self.capture.get(cv2.CAP_PROP_FPS)

    @property
    def frames(self) -> int:
        """Total amount of frames in the video"""
        return int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))

    @property
    def length(self) -> float:
        """Total length of the video in seconds"""

    @property
    def resolution(self) -> Tuple[int]:
        """Resolution of the video as a tuple (width, height)"""
        return (int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    @property
    def frame(self):
        """Current frame"""
        if self._new or self._frame is None:
            # Avoid unnecessary read operations.
            # Possible issues: Doesn't read increment the position?
            exists, frame = self.capture.read()
            if exists:
                self._frame = frame
                self._new = False
            else:
                raise IndexError('Video frame {} does not exist'.format(self.position))
        return self._frame

    def grab(self, index=None):
        """Attempts to grab frame at index and returns it

        If no index is provided, grabs the next frame.
        This is equivalent to:

            > video.position = index
            > video.frame
        """
        if not index:
            index = self.position + 1
        self.position = index
        return self.frame

    def reset(self):
        """Resets a stopped Video.

        Technically this breaks the iterator specification as iterators are not
        supposed to return anything after raising a StopIteration.
        """
        self.position = 0
        self.stopped = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.position > self.frames:
            self.stopped = True
        if self.stopped:
            self.capture.release()
            raise StopIteration
        else:
            self.position += 1
            return self.frame

    def __repr__(self):
        return '<Video at {}>'.format(self.file_name)