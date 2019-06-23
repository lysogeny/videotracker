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

    @QtCore.pyqtSlot()
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

    def __init__(self, title, params, *args, hidden=False, image_out=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.hidden = hidden
        self.params = params
        self.image_out = image_out
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
    @values.setter
    def values(self, value: dict):
        for key in value:
            self.widgets[key]['widget'].setValue(value)

    def set_values(self, value: dict):
        """Set value attribute"""
        self.values = value

class BaseFunction(QtCore.QThread):
    """Abstract function.

    There are both a widget and a function that need to be separate objects.
    The widget can be created with the `.widget()` method. The widget will be
    automatically connected to the thread object.

    Class attributes:
        title: The title used for the widget
        params: The parameters that this function uses. A dict of params as defined in `params.py`
        hidden: A boolean indicating if the constructed widget should remain hidden.
    """
    title: str
    params: dict
    hidden: bool = False

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

    @property
    def outputs_image(self):
        """Does this output images?"""
        return 'output_image' in dir(self)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None
        self._values = {name: None for name in self.params}
        # The thread of the function
        self.setObjectName(type(self).__name__)
        #self.thread.finished.connect(self.extract)
        # We need to connect the valuechanges to a function that recomputes things.
        self.create_connections()

    def create_connections(self):
        """Creates connections for this function"""
        for input_signal in self.inputs.values():
            input_signal.changed.connect(self.call)
        self.values_changed.connect(self.call)

    def widget(self):
        """Creates the associated widget and connects it"""
        widget = FunctionWidget(self.title, self.params,
                                hidden=self.hidden,
                                image_out=self.outputs_image)
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

    @QtCore.pyqtSlot(dict)
    def set_values(self, value: dict):
        """Sets the value attribute"""
        self.values = value

    def run(self):
        """Runs the thread event loop"""
        logging.info('Thread %s Started', self.title)
        self.function()
        logging.info('Thread %s Finished', self.title)

    @QtCore.pyqtSlot()
    def call(self):
        """Call to the function.

        Will only compute if none of the inputs are None.
        """
        conditions = [
            self.inputs[key].data is not None
            for key in self.inputs
        ]
        #logging.debug("This thread: %s %s", self.currentThread(), int(self.currentThreadId()))
        if all(conditions):
            if self.isRunning():
                logging.debug('previously running %s', self.title)
                #self.terminate()
            logging.debug('Computing %s', self.title)
            self.start()
        else:
            logging.debug('%i Inputs are None, not computing %s',
                          len(conditions) - sum(conditions), self.title)

    def function(self):
        """A function"""
        raise NotImplementedError

class ImageToImage(BaseFunction):
    """Image in, Image out"""
    # pylint: disable=abstract-method
    # This class is still abstract.
    def __init__(self, *args, **kwargs):
        self.input_image = Input()
        self.output_image = Output()
        super().__init__(*args, **kwargs)

class DataToData(BaseFunction):
    """Data in, Data out"""
    # pylint: disable=abstract-method
    # This class is still abstract
    def __init__(self, *args, **kwargs):
        self.input_data = Input()
        self.output_data = Output()
        super().__init__(*args, **kwargs)

class ImageToData(BaseFunction):
    """Image in, Data out"""
    # pylint: disable=abstract-method
    # This class is still abstract
    def __init__(self, *args, **kwargs):
        self.input_image = Input()
        self.output_data = Output()
        super().__init__(*args, **kwargs)
