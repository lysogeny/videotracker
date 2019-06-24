"""Special functions"""

import logging

from PyQt5 import QtCore

from .abc import Data, BaseFunction
from . import params
from .. import video

class SpecialBaseFunction(QtCore.QThread):
    """Special function base

    Special functions are mostly inputs and outputs.
    """
    params = {}
    hidden: bool = True

    @property
    def values(self) -> dict:
        """Values of this function"""
        return self.params
    @values.setter
    def values(self, value: dict):
        self.params = value

    @property
    def io(self) -> dict:
        """Inputs and outputs of this function"""
        # pylint: disable=invalid-name
        return {
            attribute: getattr(self, attribute)
            for attribute in dir(self)
            if attribute.startswith('output_')
            or attribute.startswith('input_')
        }
    @property
    def inputs(self) -> dict:
        """Inputs of this function"""
        return {
            attribute: self.io[attribute]
            for attribute in self.io
            or attribute.startswith('input_')
        }
    @property
    def outputs(self) -> dict:
        """Outputs of this function"""
        return {
            attribute: self.io[attribute]
            for attribute in self.io
            if attribute.startswith('output_')
        }



class InputFunction(SpecialBaseFunction):
    """Input function base class

    These are input functions
    """
    def __init__(self, *args, **kwargs):
        self.setup()
        super().__init__(*args, **kwargs)

    def call(self):
        self.output_image.data = self.video.frame

    def setup(self):
        """Set the input up"""
        import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
        self.video = video.Video('/home/jooa/Video/output.mp4')

    def destroy(self):
        """Destroy self"""

class InputImage(InputFunction):
    title: str = 'Input Image'
    params: dict = {
        'frame': 0,
        'file': str,
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        self.video = None
        self.output_image = Data()
        self.output_data = Data()
        self.output_data.data = {
            'frame':None,
            'timestamp':None,
            'max_frames':None,
        }
        super().__init__(*args, **kwargs)

    @property
    def frame(self) -> int:
        """The position in frames"""
        return self.video.position
    @frame.setter
    def frame(self, value: int):
        self.video.position = value

    @property
    def file_name(self) -> str:
        """The file represented by this object"""
        return self.video.file_name
    @file_name.setter
    def file_name(self, value: str):
        self.video = video.Video(value)

    def setup(self):
        """Sets the input image function up"""
        #self.video = video.Video(self.file_name)

    def function(self):
        """Gets input images"""
        self.output_image.data = self.video.frame

    def destroy(self):
        """Closes connections"""
        self.video.close()

class OutputFunction(SpecialBaseFunction):
    """Output function base class

    These are output functions
    """

class OutputImage(OutputFunction):
    """Outputs an image"""
    title: str = 'Output Image'
    params: dict = {
        'file': params.FileOpenParam(label='File'),
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_image = Data()

    def function(self):
        pass

class OutputCSV(OutputFunction):
    title: str = 'Output Data'
    params: dict = {
        'file': params.FileSaveParam(label='File'),
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_data = Data()

    def function(self):
        pass
