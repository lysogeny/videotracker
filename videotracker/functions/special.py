"""Special functions"""

import logging
import csv

from PyQt5 import QtCore
import cv2

from .abc import Data
from .. import video

class SpecialBaseFunction(QtCore.QThread):
    """Special function base

    Special functions are mostly inputs and outputs.
    """
    hidden: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict()

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

    def call(self):
        """Call run by the parent.

        Usually contains a call to function and some checks to see if it should be run.
        """
        raise NotImplementedError

    def function(self):
        """Function that does something. Main meat of the operation"""
        raise NotImplementedError

class InputFunction(SpecialBaseFunction):
    """Input function base class

    These are input functions
    """
    #pylint: disable=abstract-method
    # This class is still abstract
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
    """Input video file"""
    title: str = 'Input Image'
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params['frame'] = 0
        self.params['file'] = None
        self.video = None
        self.output_image = Data()
        self.output_meta = Data()
        self.output_meta.data = {
            'frame': None,
            'timestamp': None,
            'max_frames': None,
            'fourcc': None,
            'resolution': None,
            'framerate': None,
        }
        self.first_time = True
        self.setup()

    @property
    def frame(self) -> int:
        """The position in frames"""
        if self.video is not None and hasattr(self.video, 'capture'):
            return self.video.position
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
        if self.video is not None and self.video.file_name is not None:
            self.video.close()
        self.video = video.Video(value)
        logging.debug('Video set to `%s`', value)

    def call(self):
        """Function is only run when video is not None"""
        if self.video is None:
            logging.debug('%s does no computation as no video device exists', self.title)
        elif self.video.file_name is None:
            logging.debug('%s does no computation as video device has no file', self.title)
        elif self.frame == self.values['frame'] and self.output_image.data is not None:
            logging.debug('%s does no computation as computation has already been performed',
                          self.title)
        elif self.output_image.data is None:
            logging.debug('%s does computation, as result does not exist', self.title)
            self.function()
        else:
            logging.debug('%s does computation as no reason exists not to', self.title)
            self.function()

    def setup(self):
        """Sets the input image function up"""
        logging.debug('self.setup has been called')
        if self.file_name:
            self.video = video.Video(self.file_name)

    def initial_data(self):
        """Gets some initial data from the video"""
        logging.info('Get initial metadata from video')
        # The first three are trivial
        self.output_meta.data['framerate'] = self.video.framerate
        self.output_meta.data['fourcc'] = self.video.fourcc
        self.output_meta.data['resolution'] = self.video.resolution
        # The last involves scrolling to the end
        self.video.capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0)
        # And looking at the position
        self.output_meta.data['max_frames'] = self.video.position
        # See also helpers.get_max_frames
        self.video.reset()
        self.first_time = False
        logging.debug('Got data: %s', self.output_meta.data)

    def function(self):
        """Gets input images"""
        if self.first_time:
            self.initial_data()
        distance = self.values['frame'] - self.video.position
        logging.debug('Distance to frame is %i', distance)
        # next() on a video is very very fast. With some distance
        # threshold (here 16), you can get the appropriate frame using next() instead of
        # setting position and then loading.
        last = False
        if 0 < distance < 16:
            for i in range(distance):
                logging.debug('Getting frame %i iteration %i', self.values['frame'], i)
                try:
                    data = next(self.video)
                except StopIteration:
                    logging.debug('Encountered StopIteration at %i', self.video.position)
                    last = True
            if not last:
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
    #pylint: disable=abstract-method
    # This class is still abstract
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = {
            'file': None,
        }
        self.enabled = False

    @property
    def file_name(self):
        """The target file name"""
        return self.values['file']
    @file_name.setter
    def file_name(self, value: str):
        self.values['file'] = value

    def enable(self):
        """Enables the output"""
        self.enabled = True

    def disable(self):
        """Disables the output"""
        self.enabled = False

    def call(self):
        """Call is only run when al inputs are not None"""
        if self.enabled:
            logging.debug('%s is enabled, writing', self.title)
            self.function()
        else:
            logging.debug('%s is disabled, not writing', self.title)

class OutputImage(OutputFunction):
    """Outputs an image"""
    title: str = 'Output Image'
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = {
            'file': None,
        }
        self.input_meta = Data()
        self.input_image = Data()
        self.vid_writer = None

    def enable(self):
        """Enables the output"""
        meta = self.input_meta.data
        self.vid_writer = cv2.VideoWriter(
            self.file_name,
            cv2.VideoWriter_fourcc(*meta['fourcc']),
            meta['framerate'],
            meta['resolution'],
        )
        super().enable()
        logging.debug('Constructed %s', self.title)

    def disable(self):
        """Disables the output"""
        super().disable()
        self.vid_writer.release()
        logging.debug('Deconstructed %s', self.title)

    def function(self):
        """Function that creates output video into a file"""
        conv = cv2.cvtColor(self.input_image.data, cv2.COLOR_BGR2RGB)
        self.vid_writer.write(conv)

class OutputCSV(OutputFunction):
    """Outputs csv data"""
    title: str = 'Output Data'
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_data = Data()
        self.input_fields = Data()
        self.csv_writer = None
        self.out_connection = None

    def enable(self):
        self.out_connection = open(self.file_name, 'w')
        self.csv_writer = csv.DictWriter(self.out_connection, self.input_fields.data)
        self.csv_writer.writeheader()
        super().enable()
        logging.debug('Constructed %s', self.title)

    def disable(self):
        self.csv_writer = None
        self.out_connection.close()
        super().disable()
        logging.debug('Deconstructed %s', self.title)

    def function(self):
        """Writes a row to the csv_writer if it is enabled"""
        for row in self.input_data.data:
            self.csv_writer.writerow(row)
