"""Various segmentation methods


Stacks. Stacks have various functions associated with them.

A function has some widgets associated with it, which provide the function's
values. The only values not defined by the widgets are the function's inputs,
i.e. images. The widget thus has a valueChanged signal that is emitted when
anything changes. This should trigger a recomputation of the image results.
The other signal a function has, the results_changed, is emitted when the
computation is completed. This signal should then be connected to the next
function, as defined in the stack's dependency graph.

The stack's dependency graph is a directed graph. It should be built in reverse,
meaning that for each function, the functions that need to run before it are
defined.
The dependency graph is then used to connect the results_changed signals to the
appropriate function methods.

So what specifically is the method I need to connect to? Both valueChanged and
results_changed need some type of slot to connect to. The problem herein lies
with the slot not having any idea of where the inputs for it are.  The __call__
method of the function's probably should use some reference to the previous
result.  We thus also need a input property for each function. This property is
then used by __call__ to calculate the next result.

If you have graphviz and the graphviz module installed, you can use the stack's
dot_graph method to generate a dot language representation of the stack.

"""

#import json
#import csv
import time
import logging
import csv

from PyQt5 import QtWidgets, QtCore

import cv2

from .video import Video
from . import functions
from .functions import special
from .functions import abc

class StackWidget(QtWidgets.QWidget):
    """A widget that represents a stack"""
    valueChanged = QtCore.pyqtSignal(dict)
    view_changed = QtCore.pyqtSignal(str)

    def __init__(self, widgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widgets = widgets
        self.enabled = self._enabled = True
        self.create_gui()

    def create_gui(self):
        """Creates the widget's GUI"""
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        for widget in self.widgets:
            if not self.widgets[widget].hidden:
                self.layout.addWidget(self.widgets[widget])
                self.widgets[widget].valueChanged.connect(self.emit)
        titles = [
            (widget, self.widgets[widget].title)
            for widget in self.widgets
            if self.widgets[widget].image_out
            #if not self.widgets[widget].hidden
        ]
        im_choice = ImageChoiceWidget(titles)
        self.layout.addWidget(im_choice)
        im_choice.valueChanged.connect(self.view_changed.emit)

    def emit(self):
        """Emits current value dictionary"""
        self.valueChanged.emit(self.values)

    @property
    def values(self) -> dict:
        """Values of this widget"""
        return {
            widget: self.widgets[widget].values for widget in self.widgets
        }
    @values.setter
    def values(self, value: dict):
        for key in value:
            self.widgets[key].values = value[key]

    def set_values(self, value: dict):
        """Set value attribute of this object"""
        self.values = value

    @property
    def enabled(self) -> bool:
        """State of the widget"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        for widget in self.widgets:
            self.widgets[widget].setEnabled(value)

class ImageChoiceWidget(QtWidgets.QGroupBox):
    """A widget for image choices"""

    valueChanged = QtCore.pyqtSignal(str)

    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices
        self.create_gui()
        self.widget.currentIndexChanged.connect(self.emit)

    def create_gui(self):
        """Constructs the gui"""
        self.setTitle('Image View')
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(QtWidgets.QLabel('Output'), 0, 0)
        self.widget = QtWidgets.QComboBox()
        for choice, title in self.choices:
            self.widget.addItem(title, choice)
        self.layout.addWidget(self.widget, 0, 1)

    def emit(self):
        """Emits change of current value"""
        self.valueChanged.emit(self.widget.currentData())

class BaseStack(QtCore.QThread):
    """An abstract stack of function"""
    output_changed = QtCore.pyqtSignal()  # Computational output(s) have changed
    view_changed = QtCore.pyqtSignal() # The view has changed.
    pos_changed = QtCore.pyqtSignal(int) # Position of the video has changed.
    complete = QtCore.pyqtSignal()

    # These describe the Stack.
    methods = {}
    method_graph = {}
    method_order = []

    def __init__(self, *args, in_file=None, csv_file=None, vid_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        # These two are no longer properties, as they don't need anything to
        # happen on setting or loading.
        self._running = False
        self._enabled = False
        self._view = None
        self.stopping = False
        self.create_methods()
        self.connect_methods()
        self.connect_special()
        self._inputs = {
            fun: self.methods[fun].inputs for fun in self.methods
        }
        self._outputs = {
            fun: self.methods[fun].outputs for fun in self.methods
        }
        self.output_views = {
            output: self._outputs[output]['output_image'] for output in self._outputs
            if 'output_image' in self._outputs[output]
        }
        self.view = self.output_views['morphology']
        self.in_file = in_file
        self.csv_file = csv_file
        self.vid_file = vid_file

    def create_methods(self):
        """Constructs methods for this method"""
        self.threads = {}
        for method in self.methods:
            meth = self.methods[method] = self.methods[method]()
            thread = self.threads[method] = QtCore.QThread()
            thread.setObjectName(method)
            meth.moveToThread(thread)
            thread.start()

    def construct_graph(self):
        """Reshapes self.method_graph into list of tuples form"""
        for end in self.method_graph:
            starts = self.method_graph[end]
            if isinstance(starts, tuple):
                for start in starts:
                    yield (end, start)
            else:
                yield (end, starts)

    def connect_methods(self):
        """Connects the methods for this function stack"""
        for end, start in self.construct_graph():
            print(f'{start} → {end}')
            start_set = {method.split('_')[-1] for method in self.methods[start].outputs.keys()}
            end_set = {method.split('_')[-1] for method in self.methods[end].inputs.keys()}
            conn_type = start_set.intersection(end_set)
            logging.info('There are %i connections possible.', len(conn_type))
            for connection in conn_type:
                # Make it something. None will not work, as that is a
                # nullpointer.
                # Starts are more important than ends.
                data = getattr(self.methods[start], f'output_{connection}')
                setattr(self.methods[end], f'input_{connection}', data)

    def connect_special(self):
        """Find special nodes"""
        special_nodes = [
            self.methods[method] for method in self.methods
            if isinstance(self.methods[method], functions.special.SpecialBaseFunction)
        ]
        inputs = [
            method for method in special_nodes
            if isinstance(method, functions.special.InputFunction)
        ]
        outputs = [
            method for method in special_nodes
            if isinstance(method, functions.special.OutputFunction)
        ]
        image_inputs = [
            method for method in inputs
            if isinstance(method, functions.special.InputImage)
        ]
        image_outputs = [
            method for method in outputs
            if isinstance(method, functions.special.OutputImage)
        ]
        csv_outputs = [
            method for method in outputs
            if isinstance(method, functions.special.OutputCSV)
        ]
        if len(image_inputs) > 1:
            raise NotImplementedError('Multi image inputs are currently not implemented')
        if len(image_outputs) > 1:
            raise NotImplementedError('Multi image outputs are currently not implemented')
        if len(csv_outputs) > 1:
            raise NotImplementedError('Multi CSV outputs are currently not implemented')
        if image_inputs:
            self.image_input = image_inputs[0]
        if image_outputs:
            self.image_output = image_outputs[0]
        if csv_outputs:
            self.csv_output = csv_outputs[0]

    def dot_graph(self, file_name):
        """Returns a dot language representation of the stack"""
        from graphviz import Digraph
        graph = Digraph(comment=f'{type(self).__name__}')
        for node in self.methods:
            method = self.methods[node]
            graph.node(node, f'{method.title}')
        for end, start in self.construct_graph():
            if end.startswith('output'):
                graph.node(end)
                data_type = end.split('_')[-1]
            if start.startswith('input'):
                graph.node(start)
                data_type = start.split('_')[-1]
            if not start.startswith('input') and not end.startswith('output'):
                start_set = {method.split('_')[-1] for method in self.methods[start].outputs.keys()}
                end_set = {method.split('_')[-1] for method in self.methods[end].inputs.keys()}
                data_type = list(start_set.intersection(end_set))[0]
            logging.debug('%s → %s (%s)', start, end, data_type)
            graph.edge(start, end, label=data_type)
        return graph.render(file_name)

    def widget(self):
        """Construct a StackWidget widget"""
        widgets = {
            method: self.methods[method].widget() for method in self.methods
            if not isinstance(self.methods[method], special.SpecialBaseFunction)
        }
        widget = StackWidget(widgets)
        widget.view_changed.connect(self.set_view)
        self.values = widget.values
        widget.valueChanged.connect(self.call)
        return widget

    def set_view(self, name: str):
        """Sets the view attribute to the output identified by name"""
        self.view = self.output_views[name]
        #self.view_changed.emit()

    @property
    def view(self):
        """The view that was chosen by the user."""
        return self._view
    @view.setter
    def view(self, view):
        self._view = view
        self.view_changed.emit()

    @property
    def in_file(self) -> str:
        """The input file"""
        return self.image_input.file_name
    @in_file.setter
    def in_file(self, value: str):
        if value is not None:
            self.image_input.reset()
            self.image_input.file_name = value
        self.call()

    @property
    def pos(self) -> int:
        """Position in the video file"""
        return self.image_input.frame
    @pos.setter
    def pos(self, value: int):
        if value is not None:
            self.image_input.frame = value
            self.call()
    @QtCore.pyqtSlot(int)
    def set_pos(self, index: int):
        """Sets position of video to index"""
        self.pos = index

    @property
    def running(self) -> bool:
        """The running state. True indicates a segmentation is running"""
        return self._running
    @running.setter
    def running(self, value: bool):
        self._running = value
        if value:
            pass
        else:
            self.stop()

    @property
    def values(self) -> dict:
        """Values provided by subservient functions"""
        return {
            method: self.methods[method].values
            for method in self.methods
        }
    @values.setter
    def values(self, value: dict):
        for method in value:
            self.methods[method].values = value[method]

    def set_values(self, value: dict):
        """Sets values attribute"""
        self.values = value

    def call(self):
        """Runs through the stack

        Uses self.method_order to figure out the order in which to call methods
        """
        for method in self.method_order:
            if not self.stopping:
                self.methods[method].call()
        self.output_changed.emit()

    def stop(self):
        """Sets the stopping value, indicating that the thread should be stopped"""
        self.stopping = True

    def progress(self):
        """Returns a float ranging from 0-1 indicating progress"""
        meta = self.image_input.output_meta.data
        return meta['frame'] / meta['max_frames']

    def run(self):
        """Runs this thread"""
        logging.info('%s Started', type(self).__name__)
        self.image_input.reset()
        meta = self.image_input.output_meta.data
        frame = meta['frame']
        max_frame = meta['max_frames']
        self.stopping = False
        while frame <= max_frame and not self.stopping:
            logging.debug('Currently running frame %05i/%05i', frame, max_frame)
            self.pos_changed.emit(frame)
            meta = self.image_input.output_meta.data
            frame = meta['frame']
            max_frame = meta['max_frames']
            self.pos += 1
            self.call()
            if self.stopping:
                break
        if self.stopping:
            logging.debug('Stopped by value')
        logging.info('%s Finished', type(self).__name__)

class ThresholdStack(BaseStack):
    """A function stack for adaptive thresholds"""
    # List of functions that this class has
    methods = {
        'image_output': functions.special.OutputImage,
        'data_output': functions.special.OutputCSV,
        'bgr2gray': functions.BGR2Gray,
        'gaussian_blur': functions.GaussianBlur,
        'adaptive_threshold': functions.AdaptiveThreshold,
        'morphology': functions.Morphology,
        'contour_extract': functions.Contours,
        'size_filter': functions.SizeFilter,
        'draw_contours': functions.DrawContours,
        'feature_extraction': functions.ExtractPolygonFeatures,
        'image_input': functions.special.InputImage,
    }
    # Description of the dependency tree.
    # Disappointingly, this actually needs to be a graph, because otherwise we
    # can't figure out what goes where for non-monadic functions.
    # method_graph describes how the signal's and slots from the different
    # functions are connected.
    method_graph = {
        'image_output': 'draw_contours',
        'data_output': 'feature_extraction',
        'feature_extraction': ('size_filter', 'image_input'),
        'draw_contours': ('bgr2gray', 'size_filter'),
        'size_filter': 'contour_extract',
        'contour_extract': 'morphology',
        'morphology': 'adaptive_threshold',
        'adaptive_threshold': 'gaussian_blur',
        'gaussian_blur': 'bgr2gray',
        'bgr2gray': 'image_input',
    }
    # Method order can likely be inferred from the graph above.
    # For now, I shall just manually define the order in which things need to be
    # run
    method_order = [
        'image_input',
        'bgr2gray',
        'gaussian_blur',
        'adaptive_threshold',
        'morphology',
        'contour_extract',
        'size_filter',
        'draw_contours',
        'feature_extraction',
        'image_output',
        'data_output',
    ]

class SimpleThresholdStack(BaseStack):
    """Threshold stack, simplified

    This variant of the adaptive thresholding stack offers much more simplicity.
    Especially useful for new users.
    """

    methods = {
        'pre': functions.threshold.PreProcessor,
        'at': functions.AdaptiveThreshold,
        'post': functions.threshold.PostProcessor,
        'gray': functions.BGR2Gray,
    }
    method_graph = {
        'output_image': 'post',
        'output_data': 'post',
        'post': ('at', 'gray'),
        'at': 'pre',
        'pre': 'gray',
        'gray': 'input_image',
    }

class NullStack(BaseStack):
    """A stack that does nothing.

    No really, nothing is implemented here.
    """
