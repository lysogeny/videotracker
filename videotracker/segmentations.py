"""Various segmentation methods"""

import json

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QPushButton,
                             QComboBox, QHBoxLayout, QFileDialog)

import cv2

from .properties import Argument

class Function(QWidget):
    """Function abstraction

    Functions are defined by subclassing this class and setting attributes
    properties and function.

    """
    def __init__(self):
        super().__init__()
        self.value_file = None
        self.widgets = {}
        self.names = []
        self.layout = QVBoxLayout()
        for prop in self.arguments:
            prop.create_widget()
            self.layout.addWidget(prop.widget)
            self.widgets[prop.name] = prop.value_widget
            self.widgets[prop.name].setValue(prop.default)
            #self.widgets[prop.name].valueChanged.connect(self.message)
            self.names.append(prop.name)
        bottombox = QHBoxLayout()
        button_load = QPushButton('Load...', clicked=self.load_values)
        button_save = QPushButton('Save...', clicked=self.save_values)
        bottombox.addWidget(button_load)
        bottombox.addWidget(button_save)
        self.layout.addLayout(bottombox)
        self.setLayout(self.layout)

    def load_values(self):
        """Spawns a file picker dialog to load values"""
        file_name = QFileDialog.getOpenFileName(self, 'Load values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.load(file_name[0])

    def save_values(self):
        """Spawns a file picker dialog to save values"""
        file_name = QFileDialog.getSaveFileName(self, 'Save values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.save(file_name[0])

    def load(self, file_name):
        """Loads a file of value"""
        with open(file_name, 'r') as conn:
            values = json.load(conn)
        self.values = values

    def save(self, file_name):
        """Loads a file of value"""
        with open(file_name, 'w') as conn:
            json.dump(self.values, conn)

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

class ThresholdSegmentation(Function):
    """A threshold segmentation widget"""

    arguments = [
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
        Argument(label='Kernel size',
                 name='kernel_size',
                 form=QSpinBox,
                 default=5,
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

    def function(self, img, blur=9, size=11, c_value=3, kernel_size=5, min_size=0, max_size=1000):
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
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
        contours = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = [contour for contour in contours
                    if min_size < cv2.contourArea(contour) < max_size]
        return contours

class GaussianBlur(Function):
    """A Gausian blur"""
    arguments = [
        Argument(label='Kernel Size',
                 name='kernel',
                 form=QSpinBox,
                 default=9,
                 validity=lambda x: not x % 2),
        Argument(label='Sigma',
                 name='sigma',
                 form=QSpinBox,
                 default=9),
    ]
    function = cv2.GaussianBlur

class AdaptiveThreshold(Function):
    """Adaptive threshold"""
    arguments = [
        Argument(label='Block Size',
                 name='blockSize',
                 form=QSpinBox,
                 default=3,
                 validity=lambda x: not x % 2),
        Argument(label='C',
                 name='C',
                 form=QSpinBox,
                 default=1),
        Argument(label='Method',
                 name='adaptiveMethod',
                 form=QComboBox),
        Argument(label='Type',
                 name='thresholdType',
                 form=QComboBox),
    ]
    function = cv2.adaptiveThreshold

class FunctionStack(QWidget):
    """A stack of functions

    Ideally a list of objects inheriting from BaseFunction.

    Each Function is displayed in the order that they are added in, with a button below.
    """
    def __init__(self):
        super().__init__()
        self.results = []
        self.selected = 0
        self.create_gui()

    def create_gui(self):
        """Creates the GUI"""
        layout = QVBoxLayout()
        for function in self.functions:
            button = QPushButton('View', clicked=self.enable_view)
            layout.addWidget(function)
            layout.addWidget(button)
        self.setLayout(layout)

    def enable_view(self, index):
        """Enables output viewing for function at index"""
        # So not complete.
        self.selected = index
        # Steps necessary:
        # - Find out who sent the signal (see that tutorial)
        # - Enable all buttons
        # - Disable sender
        # - some other magic
        # - recompute?
        # - send signal to reload?

    def compute(self, img, complete=False):
        """Calculates through the stack"""
        last = img
        for index, function in enumerate(self.functions):
            self.results[index] = function(last)
            last = self.results[index]
            if index == self.selected and not complete:
                break
