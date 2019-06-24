"""Parameters used by functions

These parameters provide methods for constructing widgets and labels for a
QGridLayout.
"""

from dataclasses import dataclass
from types import MethodType
from typing import Callable

from PyQt5 import QtWidgets

from .. import widgets

# Parameters
@dataclass
class BaseParam:
    """Parameter base

    Subclass this to create a parameter that can create a widget when called
    with .widget()
    widget_callable is the type of widget to define. If the widget does not
    provide the value property (setValue, valueChanged, value), You need to
    manually define .widget (see ChoiceParam for an example).
    The most common types of parameter are however defined (see methods below).

    Defining your own custom parameter type is done by having a dataclass
    inherit from BaseParam. In that dataclass you define a series of values
    which can be used in the widget_callable's constructor.

    In practical terms this means that you look for a widget that you would like
    to have as a parameter, and have the values

    """
    label: str = ''
    widget_callable: Callable = QtWidgets.QWidget

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
            'label': QtWidgets.QLabel(self.label),
        }

@dataclass
class IntParam(BaseParam):
    """Integer Parameter"""
    widget_callable: Callable = QtWidgets.QSpinBox
    minimum: int = 0
    maximum: int = 100
    value: int = minimum
    singleStep: int = 1

@dataclass
class FloatParam(IntParam):
    """Integer Parameter"""
    widget_callable: Callable = QtWidgets.QDoubleSpinBox
    label: str = ''

@dataclass
class ColorParam(BaseParam):
    """Parameter for a colour"""
    widget_callable: Callable = widgets.ColorButton
    color: str = '#ff0000'
    label: str = 'Colour'

@dataclass
class FileOpenParam(BaseParam):
    """Paramater for an input file"""
    widget_callable: Callable = widgets.FileOpenButton
    label: str = 'Input File'

@dataclass
class FileSaveParam(BaseParam):
    """Paramater for an output file"""
    widget_callable: Callable = widgets.FileSaveButton
    label: str = 'Output File'

@dataclass
class ChoiceParam(BaseParam):
    """Choice Parameter"""
    widget_callable: Callable = QtWidgets.QComboBox
    label: str = ''
    choices: tuple = tuple()
    labels: tuple = tuple()

    def widget(self):
        """Creates a widget dictionary"""
        dictionary = {'label': QtWidgets.QLabel(self.label)}
        widget = dictionary['widget'] = QtWidgets.QComboBox()
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

@dataclass
class CheckParam(BaseParam):
    """Checkbox Parameter"""
    widget_callable: Callable = QtWidgets.QCheckBox
    label: str = ''

    def widget(self):
        widget = super().widget()
        widget['widget'].valueChanged = widget['widget'].stateChanged
        widget['widget'].value = widget['widget'].checkState
        widget['widget'].setValue = widget['widget'].setCheckState
        return widget
