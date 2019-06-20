"""Abstract base classes for functions"""

import logging

from PyQt5 import QtCore, QtWidgets

class WorkerThread(QtCore.QThread):
    """A worker thread, that is run by the functions"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def run(self):
        """Runs the parent's method called function"""
        self.parent.function()

class BaseIO(QtCore.QObject):
    """Abstract data"""

    changed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = None

    @property
    def data(self):
        """The data of this object"""
        return self._data
    @data.setter
    def data(self, value):
        self._data = value
        self.changed.emit()

class Input(BaseIO):
    """Input data"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Source should be an Output
        self._source = None

    @property
    def source(self):
        """The source for this input. Where to copy things from?

        This should be an object of class Output, or anything else that has a `data` attribute.
        """
        return self._source
    @source.setter
    def source(self, value):
        try:
            self._source.changed.disconnect(self.get)
            # Both exceptions indicate the connection did not exist previously,
            # thus pass.
        except TypeError:
            pass
        except AttributeError:
            pass
        self._source = value
        self._source.changed.connect(self.get)

    def get(self):
        """Sets the data"""
        if self.source:
            self.data = self.source.data

class Output(BaseIO):
    """Output data"""

class FunctionWidget(QtWidgets.QGroupBox):
    """Widgets for functions

    This is a qgroupbox with a qgridlayout of labels and widgets in it.
    a valueChanged signal emits a signal everytime a value is changed with a
    dict of values for this widget.
    Constructed by providing a title for the qgroupbox and a dict of params (see params for params)
    """
    valueChanged = QtCore.pyqtSignal(dict)

    def __init__(self, title, params, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.params = params
        self.create_gui()

    def create_gui(self):
        """Creates the widget of this function"""
        layout = QtWidgets.QGridLayout()
        self.widgets = {
            param: self.params[param].widget() for param in self.params
        }
        for row, param in enumerate(self.widgets):
            sub_widget = self.widgets[param]
            sub_widget['widget'].valueChanged.connect(self.emit)
            layout.addWidget(sub_widget['widget'], row, 1)
            layout.addWidget(sub_widget['label'], row, 0)
        self.setLayout(layout)
        self.setTitle(self.title)

    def emit(self):
        """Emits the valueChanged signal"""
        self.valueChanged.emit(self.values)

    @property
    def values(self) -> dict:
        """Values of this widget"""
        return {
            param: self.widgets[param]['widget'].value()
            for param in self.widgets
        }

class BaseFunction(QtCore.QThread):
    """Abstract function.

    There are both a widget and a function that need to be separate objects.
    The widget can be created with the `.widget()` method. The widget will be
    automatically connected to the thread object.
    """
    title: str
    params: dict

    values_changed = QtCore.pyqtSignal(dict)

    @property
    def io(self):
        """Gets attributes of self which inherit BaseIO"""
        #pylint: disable=invalid-name
        return {
            attribute: getattr(self, attribute)
            for attribute in dir(self)
            if not attribute in ('io', 'outputs', 'inputs')
            and isinstance(getattr(self, attribute), BaseIO)
        }

    @property
    def outputs(self):
        """Gets attributes of self which are outputs"""
        return {attribute: getattr(self, attribute)
                for attribute in self.io
                if isinstance(getattr(self, attribute), Output)}

    @property
    def inputs(self):
        """Gets attributes of self which are inputs"""
        return {attribute: getattr(self, attribute)
                for attribute in self.io
                if isinstance(getattr(self, attribute), Input)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None
        self._values = {name: None for name in self.params}
        # The thread of the function
        self.setObjectName(type(self).__name__)
        #self.thread.finished.connect(self.extract)
        # We need to connect the valuechanges to a function that recomputes things.
        self.values_changed.connect(self.function)
        # We also connect the input being changed to the function's call
        for input_signal in self.inputs.values():
            input_signal.changed.connect(self.function)

    def widget(self):
        """Creates the associated widget and connects it"""
        widget = FunctionWidget(self.title, self.params)
        widget.valueChanged.connect(self.set_values)
        self.values = widget.values
        return widget

    def emit(self):
        """Emits a value_changed signal"""
        self.valueChanged.emit(self.values)

    @property
    def values(self) -> dict:
        """Values of the widget"""
        return self._values
    @values.setter
    def values(self, value: dict):
        self._values = value
        self.values_changed.emit(value)

    def set_values(self, value: dict):
        """Sets the value attribute"""
        self.values = value

    def run(self):
        """Runs the thread event loop"""
        logging.info('Started Thread %s', self.title)
        self.exec_()

    def function(self):
        """A function"""
        raise NotImplementedError

class ImageToImage(BaseFunction):
    """Image in, Image out"""
    def __init__(self, *args, **kwargs):
        self.input_image = Input()
        self.output_image = Output()
        super().__init__(*args, **kwargs)
