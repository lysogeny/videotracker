"""Special functions"""

import logging

from PyQt5 import QtCore
import cv2

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
        super().__init__(*args, **kwargs)
        self.setup()

    def call(self):
        """Function is only run when input_source is not None"""
        condition = [self.input_sources[i] is not None for i in self.input_sources]
        if all(condition):
            self.function()

    def setup(self):
        """Set the input up"""

    def destroy(self):
        """Destroy self"""

class InputImage(InputFunction):
    title: str = 'Input Image'
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        self.video = None
        self.output_image = Data()
        self.output_meta = Data()
        self.params = {
            'frame': 0,
            'file': None,
        }
        self.output_meta.data = {
            'frame': None,
            'timestamp': None,
            'max_frames': None,
            'fourcc': None,
            'resolution': None,
            'framerate': None,
        }
        self.first_time = True
        super().__init__(*args, **kwargs)

    @property
    def frame(self) -> int:
        """The position in frames"""
        if self.video is not None and hasattr(self.video, 'capture'):
            return self.video.position
        else:
            return self.params['frame']
    @frame.setter
    def frame(self, value: int):
        self.values['frame'] = value

    def set_frame(self, value):
        """Sets the frame attribute

        Causes a call to the call method.
        """
        self.frame = value
        self.call()

    def reset(self):
        """Resets video"""
        self.params['frame'] = 0
        if self.video is not None:
            self.video.reset()

    @property
    def file_name(self) -> str:
        """The file represented by this object"""
        return self.values['file']
    @file_name.setter
    def file_name(self, value: str):
        self.values['file'] = value
        self.video = video.Video(value)

    def call(self):
        """Function is only run when video is not None"""
        if self.video is None:
            logging.debug('%s does no computation as no video device exists', self.title)
        elif self.video.file_name is None:
            logging.debug('%s does no computation as video device has no file', self.title)
        elif self.frame == self.values['frame'] and self.output_image.data is not None:
            logging.debug('%s does no computation as computation has already been performed', self.title)
        elif self.output_image.data is None:
            logging.debug('%s does computation, as result does not exist', self.title)
            self.function()
        else:
            logging.debug('%s does computation as no reason exists not to', self.title)
            self.function()

    def setup(self):
        """Sets the input image function up"""
        if self.file_name:
            self.video = video.Video(self.file_name)

    def initial_data(self):
        """Gets some initial data from the video"""
        # The first three are trivial
        self.output_meta.data['framerate'] = self.video.framerate
        self.output_meta.data['fourcc'] = self.video.fourcc
        self.output_meta.data['resolution'] = self.video.resolution
        # The last involves scrolling to the end
        self.video.capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0)
        # And looking at the position
        self.output_meta.data['max_frames'] = self.video.position
        # See also helpers.get_max_frames
        self.video.position = 0
        self.first_time = False

    def function(self):
        """Gets input images"""
        if self.first_time:
            self.initial_data()
        distance = self.values['frame'] - self.video.position
        logging.debug('Distance to frame is %i', distance)
        # next() on a video is very very fast. With some distance
        # threshold (here 16), you can get the appropriate frame using next() instead of
        # setting position and then loading.
        if 0 < distance < 16:
            for i in range(distance):
                logging.debug('Getting frame %i iteration %i', self.values['frame'], i)
                try:
                    data = next(self.video)
                except StopIteration:
                    logging.debug('Encountered StopIteration at %i', self.video.position)
            self.output_image.data = data
        else:
            self.video.position = self.values['frame']
            self.output_image.data = self.video.frame
        self.output_meta.data['frame'] = self.video.position
        self.output_meta.data['timestamp'] = self.video.time

    def destroy(self):
        """Closes connections"""
        self.video.close()

class OutputFunction(SpecialBaseFunction):
    """Output function base class

    These are output functions
    """
    def call(self):
        """Call is only run when al inputs are not None"""
        condition = [self.inputs[i] is not None for i in self.inputs]
        if all(condition):
            self.function()

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
