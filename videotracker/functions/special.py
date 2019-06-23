"""Special functions"""

from .abc import Input, Output
from . import params
from .. import video

class SpecialBaseFunction:
    """Special function base"""


class InputImage(SpecialBaseFunction):
    title: str = 'Input Image'
    params: dict = {
        'frame': params.IntParam(minimum=0, maximum=9999999999999, label='Frame'),
        'file': params.FileOpenParam(label='File'),
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video = None
        self.output_image = Output()

    def function(self):
        if self.video is None or self.video.file_name != self.values['file']:
            self.video = video.Video(self.values['file'])
        if self.video.position != self.values['frame']:
            self.video.position = self.values['frame']
        self.output_image.data = self.video.frame

class OutputImage(SpecialBaseFunction):
    """Outputs an image"""
    title: str = 'Output Image'
    params: dict = {
        'file': params.FileOpenParam(label='File'),
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_image = Input()

    def function(self):
        pass

class OutputData(SpecialBaseFunction):
    title: str = 'Output Data'
    params: dict = {
        'file': params.FileSaveParam(label='File'),
    }
    hidden: bool = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_data = Input()

    def function(self):
        pass
