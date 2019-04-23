"""Definitions for properties"""

from typing import Callable, Tuple
from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QSpinBox, QDoubleSpinBox

@dataclass
class BaseArgument:
    """Abstraction of segmentation method properties

    Attributes
    ----------

    name: Name used internally
    label: Label on the GUI
    default: Default value
    form: Callable that creates a QWidget
    validity: Callable that defines valid values
    type: Type of the object
    """
    name: str = ''
    label: str = ''
    default: int = 0
    form: Callable = QWidget
    validity: Callable = lambda x: True
    type: type = int

class Argument(BaseArgument):
    """A property of a segmentation method"""
    # Pylint, this is still a dataclass.
    # pylint: disable=too-few-public-methods
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = None
        self._widget = None

    @property
    def prop(self):
        """Property of the thing?"""
        return self._widget.value()
    @prop.setter
    def prop(self, value):
        if self.validity(value):
            self._widget.setValue(value)

    def create_widget(self):
        """Creates the widget for the property.

        Widget in `form` on the left, Label on right.
        """
        layout = QHBoxLayout()
        self.value_widget = self.form()
        layout.addWidget(self.value_widget)
        layout.addWidget(QLabel(self.label))
        self.widget = QWidget()
        self.widget.valueChanged = self.value_widget.valueChanged
        self.widget.setLayout(layout)

class IntegerArgument(BaseArgument):
    """Argument that is of type int"""
    # This contains a QSpinBox with a maximum range and minimum range
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = QSpinBox()

    @property
    def range(self) -> Tuple[int, int]:
        """Range of the spinbox"""
        return (self.widget.minimum(), self.widget.maximum())
    @range.setter
    def range(self, value: Tuple[int, int]):
        self.widget.setRange(value)

    @property
    def minimum(self) -> int:
        """Minimum value possible in the spinbox"""
        return self.widget.minimum()
    @minimum.setter
    def minimum(self, value: int):
        """Minimum value possible in the spinbox"""
        return self.widget.setMinimum(value)

    @property
    def maximum(self) -> int:
        """Maximum value possible in the spinbox"""
        return self.widget.maximum()
    @maximum.setter
    def maximum(self, value: int):
        """Maximum value possible in the spinbox"""
        return self.widget.setMaximum(value)

    @property
    def step(self) -> int:
        """Allowable steps of this element"""
        return self.widget.singleStep()
    @step.setter
    def step(self, value: int):
        """Allowable steps of this element"""
        return self.widget.setSingleStep(value)

class FloatArgument(BaseArgument):
    """"Argument that is of type `float`"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = QDoubleSpinBox()


class MultipleChoiceArgument(BaseArgument):
    """Argument with multiple options"""
    # We need a mapping of options to values for the function. Also pretty names and something?
