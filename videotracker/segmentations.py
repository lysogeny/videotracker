"""Various segmentation methods"""

import json
from pprint import pprint

from typing import Callable
from dataclasses import dataclass

from PyQt5.QtWidgets import (QWidget, QSpinBox, QPushButton,
                             QComboBox, QFileDialog, QGridLayout, QLabel,
                             QDoubleSpinBox)

from PyQt5.QtCore import QThread, pyqtSignal

import cv2

@dataclass
class BaseParam:
    """Parameter base"""
    label: str = ''
    widget_callable: Callable = QWidget

    def widget(self):
        """Returns a widget  dictionary: A dict with 'label' and 'widget'"""
        members = self.__dict__
        construct = {
            member: members[member] for member in members
            if not member.startswith('__')
            and member not in ('label', 'widget_callable')
        }
        return {
            'widget': self.widget_callable(**construct),
            'label': QLabel(self.label),
        }

@dataclass
class IntParam(BaseParam):
    """Integer Parameter"""
    widget_callable: Callable = QSpinBox
    minimum: int = 0
    maximum: int = 100
    value: int = minimum
    singleStep: int = 1

@dataclass
class FloatParam:
    """Integer Parameter"""
    widget_callable: Callable = QDoubleSpinBox
    label: str = ''
    minimum: float = 0
    maximum: float = 100
    singleStep: float = 1

@dataclass
class ChoiceParam:
    """Choice Parameter"""
    label: str = ''
    choices: tuple = tuple()
    labels: tuple = tuple()

    def widget(self):
        """Creates a widget dictionary"""
        dictionary = {'label': QLabel(self.label)}
        widget = dictionary['widget'] = QComboBox()
        for label, choice in zip(self.labels, self.choices):
            widget.addItem(label, choice)
        widget.valueChanged = widget.currentIndexChanged
        widget.value = widget.currentData
        return dictionary

class BaseSegmentation(QWidget, QThread):
    """Abstract segmentation"""

    params = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.values = {}
        self.value_file = ""
        self.create_widgets()
        self.create_gui()

    def create_widgets(self):
        """Creates the widgets from self.params"""
        self.widgets = {param: self.params[param].widget() for param in self.params}

    def create_gui(self):
        """Creates main gui elements"""
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        for row, widget in enumerate(self.widgets):
            self.layout.addWidget(self.widgets[widget]['widget'], row, 0)
            self.layout.addWidget(self.widgets[widget]['label'], row, 1)
        self.layout.addWidget(QPushButton('Save...', pressed=self.save_values))
        self.layout.addWidget(QPushButton('Load...', pressed=self.load_values))

    @property
    def values(self) -> dict:
        """Values configured in the segmentation method"""
        return {
            name: self.widgets[name]['widget'].value()
            for name in self.widgets
        }
    @values.setter
    def values(self, values: dict):
        for value in values:
            if value in self.widgets:
                self.widgets[value]['widget'].setValue(values[value])

    def load(self, file_name: str):
        """Loads a file of value"""
        with open(file_name, 'r') as conn:
            values = json.load(conn)
        self.values = values

    def save(self, file_name: str):
        """Loads a file of value"""
        with open(file_name, 'w') as conn:
            json.dump(self.values, conn)

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

class ThresholdSegmentation(BaseSegmentation):
    """Sample segmentation"""
    params = {
        'blur': IntParam(singleStep=2, minimum=1, maximum=100, label='Blur'),
        'thresh_type': ChoiceParam(
            choices=(cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C),
            labels=('Mean', 'Gaussian'),
            label='Threshold Type',
        ),
        'size': IntParam(singleStep=2, minimum=3, maximum=100, label='Block Size'),
        'c_value': IntParam(singleStep=1, minimum=-100, maximum=100, label='C Value'),
        'kernel_size': IntParam(singleStep=2, minimum=1, maximum=100, label='Kernel Size'),
        'min_size': IntParam(singleStep=1, maximum=1000, label='Minimum Size'),
        'max_size': IntParam(singleStep=1, maximum=1000, value=1000, label='Maximum Size'),
    }

    def function(self, img, thresh_type, blur, size, c_value, kernel_size, min_size, max_size):
        """Adaptive threshold segmentation of image

        Takes an image img
        Returns polygons
        """
        # pylint: disable=too-many-arguments,no-self-use
        # I need this many arguments, and I can't have this as not a method.
        frame = img.copy()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (blur, blur), 0)
        frame = cv2.adaptiveThreshold(frame, 255, thresh_type,
                                      cv2.THRESH_BINARY_INV, size, c_value)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
        contours = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = [contour for contour in contours
                    if min_size < cv2.contourArea(contour) < max_size]
        return contours
