"""Functions that can be used to assemble segmentations"""

from types import MethodType
from typing import Callable
from dataclasses import dataclass

import PyQt5.QtWidgets as qwidgets
from PyQt5 import QtCore

import cv2

from . import widgets

# Parameters
@dataclass
class BaseParam:
    """Parameter base

    Subclass this to create a parameter that can create a widget when called
    with .widget()
    widget_callable is the type of widget to define. If the widget does not
    provide the value property (setValue, valueChanged, value), You need to
    manually define .widget (see ChoiceParam for an example).
    The most common types of parameter are however defined (see methods below)
    """
    label: str = ''
    widget_callable: Callable = qwidgets.QWidget

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
            'label': qwidgets.QLabel(self.label),
        }

@dataclass
class IntParam(BaseParam):
    """Integer Parameter"""
    widget_callable: Callable = qwidgets.QSpinBox
    minimum: int = 0
    maximum: int = 100
    value: int = minimum
    singleStep: int = 1

@dataclass
class FloatParam(BaseParam):
    """Integer Parameter"""
    widget_callable: Callable = qwidgets.QDoubleSpinBox
    label: str = ''
    minimum: float = 0
    maximum: float = 100
    singleStep: float = 1

@dataclass
class ColorParam(BaseParam):
    """Parameter for a colour"""
    widget_callable: Callable = widgets.ColourButton
    label: str = 'Colour'

@dataclass
class ChoiceParam(BaseParam):
    """Choice Parameter"""
    widget_callable: Callable = qwidgets.QComboBox
    label: str = ''
    choices: tuple = tuple()
    labels: tuple = tuple()

    def widget(self):
        """Creates a widget dictionary"""
        dictionary = {'label': qwidgets.QLabel(self.label)}
        widget = dictionary['widget'] = qwidgets.QComboBox()
        for label, choice in zip(self.labels, self.choices):
            widget.addItem(label, choice)
        widget.valueChanged = widget.currentIndexChanged
        # setValue for QComboBox
        def set_data(self, data=None):
            """Method for setting the data of the QComboBox"""
            self.setCurrentIndex(self.findData(data))
        widget.setValue = MethodType(set_data, widget)
        widget.value = widget.currentData
        return dictionary

### FUNCTIONS ###
# Unlike the previous parts, these can inherit from QWidget.
# That is becauset they are not constructed in class attributes.

class BaseFunction(qwidgets.QGroupBox):
    """Abstract function"""
    title: str
    inputs: dict
    function: Callable

    valueChanged = QtCore.pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_gui()
        self.setTitle(self.title)

    def create_gui(self):
        """Creates the widget of this function"""
        layout = qwidgets.QGridLayout()
        self.widgets = {
            param: self.inputs[param].widget() for param in self.inputs
        }
        for row, param in enumerate(self.widgets):
            print(self.widgets)
            sub_widget = self.widgets[param]
            sub_widget['widget'].valueChanged.connect(self.emit)
            layout.addWidget(sub_widget['widget'], row, 0)
            layout.addWidget(sub_widget['label'], row, 1)
        self.setLayout(layout)
        return self

    def emit(self):
        """Emits a valueChanged signal"""
        self.valueChanged.emit(self.value)

    @property
    def value(self) -> dict:
        """Values of the widget"""
        return {
            param: self.widgets[param]['widget'].value()
            for param in self.widgets
        }

    def call(self):
        """Returns a function"""
        return self.function

class GaussianBlur(BaseFunction):
    """Blurs Gauss"""
    title = 'Gaussian Blur'
    inputs = {
        'size': IntParam(minimum=1, maximum=100, singleStep=2, label='Size'),
    }
    function = lambda x, size: cv2.GaussianBlur(x, (size, size), 0)

class AdaptiveThreshold(BaseFunction):
    """Computes an adaptive Threshold"""
    title = 'Adaptive Threshold'
    inputs = {
        'blockSize': IntParam(singleStep=2, minimum=3, maximum=100, label='Block Size'),
        'C': IntParam(singleStep=1, minimum=-100, maximum=100, label='C Value'),
        'thresholdType': ChoiceParam(
            choices=(cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C),
            labels=('Mean', 'Gaussian'),
            label='Threshold Type',
        ),
    }
    function = lambda x, options: cv2.adaptiveThreshold(x, maxValue=255,
                                                        adaptiveMethod=cv2.THRESH_BINARY_INV,
                                                        **options)

class Contours(BaseFunction):
    """Extracts contours"""
    title: str = 'Extract Contours'
    inputs: dict = {
        'mode': ChoiceParam(
            choices=(cv2.RETR_EXTERNAL, cv2.RETR_LIST, cv2.RETR_CCOMP, cv2.RETR_TREE),
            labels=('External Contours', 'All Contours', '??', 'Full Tree'),
            label='Retrieval Mode',
        ),
        'method': ChoiceParam(
            choices=(cv2.CHAIN_APPROX_NONE, cv2.CHAIN_APPROX_SIMPLE, cv2.CHAIN_APPROX_TC89_L1, cv2.CHAIN_APPROX_TC89_KCOS),
            labels=('All contour points', 'Compress segments', 'Teh-Chin L1', 'Teh-Chin KCOS'),
            label='Method',
        ),
    }
    function: Callable = cv2.findContours

class SizeFilter(BaseFunction):
    """Provides a method for size filters"""
    title: str = 'Filter by area'
    inputs: dict = {
        'minimum': IntParam(singleStep=1, maximum=1000, label='Minimum Size'),
        'maximum': IntParam(singleStep=1, maximum=1000, value=1000, label='Maximum Size'),
    }
    function: Callable = lambda x, minimum, maximum: [i for i in x
                                                      if minimum <= cv2.contourArea(i) <= maximum]

class DrawContours(BaseFunction):
    """Draws Contours"""
    title: str = 'Draw Contours'
    inputs: dict = {
        'color': ColorParam(),
        'thickness': IntParam(minimum=1, maximum=100, label='Thickness')
    }
    function: Callable = cv2.drawContours

class Morphology(BaseFunction):
    title: str = 'Morphological Operation'
    inputs: dict = {
        'ksize': IntParam(minimum=1, maximum=100, label='Kernel Size', singleStep=2),
        'shape': ChoiceParam(
            choices=(cv2.MORPH_ELLIPSE, cv2.MORPH_RECT, cv2.MORPH_CROSS),
            labels=('Ellipse', 'Rectangle', 'Cross'),
            label='Kernel Shape',
        ),
        'operation': ChoiceParam(
            choices=(cv2.MORPH_OPEN, cv2.MORPH_CLOSE, cv2.MORPH_GRADIENT,
                     cv2.MORPH_TOPHAT, cv2.MORPH_BLACKHAT),
            labels=('Open', 'Close', 'Gradient', 'Tophat', 'Blackhat'),
            label='Operation',
        )
    }
    function: Callable = lambda x, opt: cv2.morphologyEx(
        x, opt['operation'],
        cv2.getStructuringElement(opt['shape'], (opt['ksize'], opt['ksize']))
    )

