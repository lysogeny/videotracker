"""Functions for simplified threshold stack"""

import cv2

from .abc import ImageToImage, Input, Output, ImageToData, BaseFunction
from . import params


class PreProcessor(ImageToImage):
    """Preprocessor

    This is preprocessing for the thresholdstack.
    Basically gaussian blur
    """
    title: str = 'Preprocessing'
    params: dict = {
        'blur_width': params.IntParam(minimum=1, maximum=999, singleStep=2, label='Blur Size'),
        'mask_center_x': params.FloatParam(
            minimum=0, maximum=1,
            singleStep=0.01,
            label='Mask Center x',
        ),
        'mask_center_y': params.FloatParam(
            minimum=0, maximum=1,
            singleStep=0.01,
            label='Mask Center y',
        ),
    }
    def function(self):
        """Blurs"""
        self.output_image.data = cv2.GaussianBlur(
            self.input_image.data,
            (self.values['blur_width'], self.values['blur_width']),
            0
        )

class PostProcessor(BaseFunction):
    """

    This is postprocessing for the thresholdstack.
    Basically morphological opening, followed by size filtering.
    """
    title: str = 'Preprocessing'
    params: dict = {
        'ksize': params.IntParam(minimum=1, maximum=255, singleStep=2, label='Kernel Size'),
        'min_size': params.FloatParam(
            minimum=0,
            maximum=1000,
            singleStep=0.1,
            label='Minimum Size',
        ),
        'max_size': params.FloatParam(
            minimum=0,
            maximum=1000,
            singleStep=0.1,
            value=1000,
            label='Maximum Size',
        ),
    }
    def __init__(self, *args, **kwargs):
        self.input_image = Input()
        self.output_image = Output()
        self.output_data = Output()
        super().__init__(*args, **kwargs)
    def function(self):
        """Morphology"""
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.values['ksize'], self.values['ksize'])
        )
        morph = cv2.morphologyEx(self.input_image.data, cv2.MORPH_OPEN, kernel)
        cont = cv2.findContours(morph, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_SIMPLE)[0]
        cont = [i for i in cont if self.values['min_size'] <= cv2.contourArea(i) <= self.values['max_size']]
        self.output_data.data = cont
        self.output_image.data = morph
