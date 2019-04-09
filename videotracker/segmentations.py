"""Various segmentation methods"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QMessageBox, QPushButton

import cv2

from .properties import Argument

class BaseSegmentation(QWidget):
    """Segmentation abstraction

    Segmentations are defined by subclassing this class and setting attributes
    properties and function.

    """
    def __init__(self):
        super().__init__()
        self.widgets = {}
        self.names = []
        self.layout = QVBoxLayout()
        for prop in self.properties:
            prop.create_widget()
            self.layout.addWidget(prop.widget)
            self.widgets[prop.name] = prop._widget
            self.widgets[prop.name].setValue(prop.default)
            #self.widgets[prop.name].valueChanged.connect(self.message)
            self.names.append(prop.name)
        self.setLayout(self.layout)

    @property
    def values(self):
        """Collected values of all widgets

        Setting this changes the values in the respective widgets.
        """
        return {
            name: self.widgets[name].value()
            for name in self.names
        }
    @values.setter
    def values(self, values):
        for value in values:
            if value in self.names:
                self.widgets[value].setValue(values[value])

class ThresholdSegmentation(BaseSegmentation):
    """A threshold segmentation widget"""

    properties = [
        Argument(label='Blur Size',
                 name='blur',
                 form=QSpinBox,
                 default=9,
                 validity=lambda x: not x % 2),
        Argument(label='Bin Size',
                 name='size',
                 form=QSpinBox,
                 default=5,
                 validity=lambda x: not x % 2),
        Argument(label='C Value',
                 name='c_value',
                 form=QSpinBox,
                 default=10,
                 validity=lambda x: True),
        Argument(label='Min Size',
                 name='min_size',
                 form=QSpinBox,
                 default=0,
                 validity=lambda x: True),
        Argument(label='Max Size',
                 name='max_size',
                 form=QSpinBox,
                 default=100,
                 validity=lambda x: True),
    ]

    def function(self, img, blur=9, size=11, c_value=3, min_size=0, max_size=1000):
        """Adaptive threshold segmentation of image
        Takes an image img
        Returns polygons
        """
        # pylint: disable=too-many-arguments,no-self-use
        # I need this many arguments, and I can't have this as not a method.
        frame = img.copy()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (blur, blur), 0)
        frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV, size, c_value)
        contours = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = [contour for contour in contours
                    if min_size < cv2.contourArea(contour) < max_size]
        return contours
