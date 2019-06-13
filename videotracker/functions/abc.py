"""Abstract base classes for functions"""

from PyQt5 import QtCore, QtWidgets

class WorkerThread(QtCore.QThread):
    """A worker thread, that is run by the functions"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent

    def run(self):
        self.parent.function()

class BaseFunction(QtWidgets.QGroupBox):
    """Abstract function.

    This function provides the main parts for creating a function.
    A function provides a __call__ that spawns a thread to run function().
    """
    title: str
    params: dict
    inputs = {}
    #function: Callable

    valueChanged = QtCore.pyqtSignal(dict)
    # The results_changed signal is emitted after self.results is assigned.

    def get_input_signals(self, names=False):
        return []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_gui()
        self.setTitle(self.title)
        self.result = None
        # The thread of the function
        self.thread = WorkerThread(self)
        self.thread.finished.connect(lambda: print(self.title + ' Thread finished'))
        self.thread.setObjectName(self.title)
        #self.thread.finished.connect(self.extract)
        # We need to connect the valuechanges to a function that recomputes things.
        self.valueChanged.connect(self.__call__)
        # We also connect the input being changed to the function's call
        input_signals = list(self.get_input_signals())
        for input_signal in input_signals:
            input_signal.connect(self.thread.start)

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
        return self

    def emit(self):
        """Emits a value_changed signal"""
        self.valueChanged.emit(self.values)

    @property
    def values(self) -> dict:
        """Values of the widget"""
        return {
            param: self.widgets[param]['widget'].value()
            for param in self.widgets
        }

    def run(self, signal):
        result = signal.sender().result
        self.inputs[0] = result
        self()

    def __call__(self):
        """Runs this function's computation

        Currently missing are bits for running this in a separate thread.
        """
        self.thread.start()

    def extract(self):
        """Extracts stuff from the thread and sets appropriate things"""

    def function(self):
        """A function"""
        raise NotImplementedError

class BaseInput(QtCore.QObject):
    """Abstract mixin input class"""

    #input_changed = QtCore.pyqtSignal()

    def get_input_signals(self, names=False):
        """Returns all input signals of this class"""
        for attribute in dir(self):
            try:
                attr = getattr(self, attribute)
            except AttributeError:
                # Attribute error is sometimes raised because the object may be
                # in a strange state of semi-constructedness
                pass
            except KeyError:
                # Key error is raised when the underlying property does not have
                # a dict properly assigned yet. I don't always have a proper dict
                pass
            else:
                is_signal = isinstance(attr, QtCore.pyqtBoundSignal) or isinstance(attr, QtCore.pyqtSignal)
                is_input = attribute.startswith('input_')
                if is_input and is_signal:
                    if names:
                        yield attribute
                    else:
                        yield attr

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input = {}
        input_signals = self.get_input_signals(names=True)
        for input_signal in input_signals:
            self._input['_'.join(input_signal.split('_')[1:])] = None
            #getattr(self, input_signal).connect(self.input_changed.emit)

class BaseOutput(QtCore.QObject):
    """Abstract mixin output class"""

    #output_changed = QtCore.pyqtSignal()

    def get_output_signals(self, names=False):
        """Returns all output signals of this class"""
        for attribute in dir(self):
            try:
                attr = getattr(self, attribute)
            except AttributeError:
                # Attribute error is sometimes raised because the object may be
                # in a strange state of semi-constructedness
                pass
            except KeyError:
                # Key error is raised when the underlying property does not have
                # a dict properly assigned yet. I don't always have a proper dict
                pass
            else:
                is_signal = isinstance(attr, QtCore.pyqtBoundSignal) or isinstance(attr, QtCore.pyqtSignal)
                is_output = attribute.startswith('output_')
                if is_output and is_signal:
                    if names:
                        yield attribute
                    else:
                        yield attr

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._output = {}
        output_signals = self.get_output_signals(names=True)
        for output_signal in output_signals:
            self._output['_'.join(output_signal.split('_')[1:])] = None
            #getattr(self, output_signal).connect(self.output_changed.emit)

class ImageOutput(BaseOutput):
    """A mixable output image class"""

    output_image_changed = QtCore.pyqtSignal()

    @property
    def output_image(self):
        """The output image. Setting will emit output_image_changed"""
        return self._output['image']
    @output_image.setter
    def output_image(self, value):
        self._output['image'] = value
        self.output_image_changed.emit()

class ImageInput(BaseInput):
    """A mixin input image class"""

    input_image_changed = QtCore.pyqtSignal()

    @property
    def input_image(self):
        """The input image. Setting will emit input_image_changed"""
        return self._input['image']
    @input_image.setter
    def input_image(self, value):
        self._input['image'] = value
        self.input_image_changed.emit()

class DataInput(BaseInput):
    """A mixin input data class"""
    input_data_changed = QtCore.pyqtSignal()

    @property
    def input_data(self):
        """The input data"""
        return self._input['data']
    @input_data.setter
    def input_data(self, value):
        self._input['data'] = value
        self.input_data_changed.emit()

class DataOutput(BaseOutput):
    """A mixin output data class"""
    output_data_changed = QtCore.pyqtSignal()

    @property
    def output_data(self):
        """The output data"""
        return self._output['data']
    @output_data.setter
    def input_data(self, value):
        self_output['data'] = value
        self.output_data_changed.emit()
