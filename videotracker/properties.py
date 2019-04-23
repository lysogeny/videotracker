"""Definitions for properties"""

from typing import Callable
from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

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
