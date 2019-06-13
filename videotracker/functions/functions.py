"""Functions that can be used to assemble segmentations"""

import collections

import cv2

from . import params
from .abc import ImageInput, ImageOutput, DataInput, DataOutput, BaseFunction

### FUNCTIONS ###
# Unlike the previous parts, these can inherit from QWidget.
# That is becauset they are not constructed in class attributes.

class GaussianBlur(BaseFunction, ImageOutput, ImageInput):
    """Blurs Gauss"""
    title = 'Gaussian Blur'
    params = {
        'size': params.IntParam(minimum=1, maximum=101, singleStep=2, label='Size'),
    }
    # These are the variables that define the out/input
    def function(self):
        """Blurs Gaussianly"""
        self.output_image = cv2.GaussianBlur(self.input_image, (self.values['size'], self.values['size']), 0)
        return self.output_image

class AdaptiveThreshold(ImageOutput, ImageInput, BaseFunction):
    """Computes an adaptive threshold"""
    title = 'Adaptive Threshold'
    params = {
        'blockSize': params.IntParam(singleStep=2, minimum=3, maximum=101, label='Block Size'),
        'C': params.IntParam(singleStep=1, minimum=-100, maximum=100, label='C Value'),
        'adaptiveMethod': params.ChoiceParam(
            choices=(cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C),
            labels=('Mean', 'Gaussian'),
            label='Threshold Type',
        ),
    }
    def function(self):
        """Applies an adaptive threshold"""
        # This is an example of a somewhat simple function, most of the inputs
        # are mapped directly to the function itself.
        self.output_image = cv2.adaptiveThreshold(self.input_image, maxValue=255,
                                                  thresholdType=cv2.THRESH_BINARY_INV,
                                                  **self.values)
        return self.output_image

class Contours(ImageInput, DataOutput, BaseFunction):
    """Extracts contours"""
    title: str = 'Extract Contours'
    params: dict = {
        'mode': params.ChoiceParam(
            choices=(cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE),
            labels=('External Contours', 'All Contours', '??', 'Full Tree'),
            label='Retrieval Mode',
        ),
        'method': params.ChoiceParam(
            choices=(cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE,
                     cv2.CHAIN_APPROX_TC89_L1, cv2.CHAIN_APPROX_TC89_KCOS),
            labels=('All contour points', 'Compress segments', 'Teh-Chin L1', 'Teh-Chin KCOS'),
            label='Method',
        ),
    }
    def function(self):
        """Extracts contours"""
        self.output_data = cv2.findContours(self.input_image, **self.values)
        return self.output_data

class SizeFilter(DataInput, DataOutput, BaseFunction):
    """Provides a method for size filters"""
    title: str = 'Filter by area'
    params: dict = {
        'minimum': params.IntParam(singleStep=1, maximum=1000, label='Minimum Size'),
        'maximum': params.IntParam(singleStep=1, maximum=1000, value=1000, label='Maximum Size'),
    }
    def function(self, inputs):
        """Filters contours by enclosed area"""
        self.output_data = [i for i in self.input_data
                            if self.values['minimum'] <= cv2.contourArea(i) <= self.values['maximum']]
        return self.output_data

class DrawContours(DataInput, ImageInput, ImageOutput, BaseFunction):
    """Draws Contours"""
    title: str = 'Draw Contours'
    params: dict = {
        'color': params.ColorParam(),
        'thickness': params.IntParam(minimum=1, maximum=100, label='Thickness')
    }
    def function(self, inputs):
        """Draws contours"""
        self.output_image = cv2.drawContours(self.input_image, self.input_data, **self.values)
        return self.output_image

class Morphology(ImageInput, ImageOutput, BaseFunction):
    """Morphological operations"""
    title: str = 'Morphological Operation'
    params: dict = {
        'ksize': params.IntParam(minimum=1, maximum=100, label='Kernel Size', singleStep=2),
        'shape': params.ChoiceParam(
            choices=(cv2.MORPH_ELLIPSE, cv2.MORPH_RECT, cv2.MORPH_CROSS),
            labels=('Ellipse', 'Rectangle', 'Cross'),
            label='Kernel Shape',
        ),
        'operation': params.ChoiceParam(
            choices=(cv2.MORPH_OPEN, cv2.MORPH_CLOSE, cv2.MORPH_GRADIENT,
                     cv2.MORPH_TOPHAT, cv2.MORPH_BLACKHAT),
            labels=('Open', 'Close', 'Gradient', 'Tophat', 'Blackhat'),
            label='Operation',
        )
    }
    def function(self):
        """Morphological Operations"""
        kernel = cv2.getStructuringElement(self.values['shape'], (self.values['ksize'], self.values['ksize']))
        self.output_image = cv2.morphologyEx(self.input_image, self.values['operation'], kernel)
        return self.output_image
