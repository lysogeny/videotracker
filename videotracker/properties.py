"""Definitions for properties"""

from typing import Callable
from dataclasses import dataclass

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout

@dataclass
class BaseArgument:
    """Abstraction of segmentation method properties"""
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
        """Creates the widget for the property"""
        layout = QHBoxLayout()
        self._widget = self.form()
        layout.addWidget(self._widget)
        layout.addWidget(QLabel(self.label))
        self.widget = QWidget()
        self.widget.valueChanged = self._widget.valueChanged
        self.widget.setLayout(layout)
