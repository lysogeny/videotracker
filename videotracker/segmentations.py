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

"""

#import json
#import csv

from PyQt5 import QtWidgets, QtCore
#import cv2

from .video import Video, VideoThread
#from . import contours
from . import functions
from .functions import params

class BaseStack(QtWidgets.QWidget):
    """An abstract stack of function"""
    valueChanged = QtCore.pyqtSignal(dict) # The values of the widgets have changed
    output_changed = QtCore.pyqtSignal()  # Computational output(s) have changed
    view_changed = QtCore.pyqtSignal() # The chosen view has changed.
    pos_changed = QtCore.pyqtSignal(int)

    # Methods to be used and description of connections between methods to be
    # made.
    methods = {}
    method_graph = {}

    @property
    def enabled(self) -> bool:
        """State of the widget"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        for widget in self.widgets:
            self.widgets[widget].setEnabled(value)

    def set_running(self, value: bool):
        """Sets the running property

        Exists to be a slot.
        """
        self.running = value

    @property
    def running(self) -> bool:
        """The running state of the module"""
        # Todo: define how to run
        return self._running
    @running.setter
    def running(self, value: bool):
        self._running = value

    @property
    def in_file(self) -> str:
        """The input file"""
        return self.files['in']
    @in_file.setter
    def in_file(self, value: str):
        self.files['in'] = value
        if value is not None:
            self.video = Video(value)
            #self.video.start()
            self.load_frame()
        # This might cause problems, depending on what the behaviour of the
        # video object was.

    def set_pos(self, value: int):
        """Set position to value"""
        self.pos = value

    @property
    def pos(self) -> int:
        """Position in the video file"""
        return self.video.position
    @pos.setter
    def pos(self, value: int):
        self.video.position = value
        self.load_frame()

    def load_frame(self):
        """Loads current frame"""
        self.input_image.data = self.video.frame

    def __init__(self, *args, input_file=None, csv_file=None, vid_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        # These two are no longer properties, as they don't need anything to
        # happen on setting or loading.
        self.video = None
        self.files = {'in': None, 'csv': None, 'vid': None}
        self.csv_file: str = csv_file
        self.vid_file: str = vid_file
        self.input_file: str = input_file
        self._running = False
        self._enabled = False
        self.widgets = {}
        self.create_gui()
        #self.create_methods()
        self.connect_methods()
        self._inputs = {
            fun: self.methods[fun].input_image for fun in self.methods
        }
        self._outputs = {
            fun: self.methods[fun].output_image for fun in self.methods
        }
        self.view = self._outputs['morphology']
        self.display()

    @property
    def outputs(self):
        """Output of all variables here"""
        return {output: self._outputs[output].data for output in self._outputs}

    def create_gui(self):
        """Creates the widget of this method stack"""
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.methods = self.widgets = {
            function: self.methods[function]() for function in self.methods
        }
        for widget in self.widgets:
            self.widgets[widget].valueChanged.connect(self.valueChanged.emit)
            layout.addWidget(self.widgets[widget])
        box = QtWidgets.QGroupBox('Other options')
        widgets = params.ChoiceParam(
            choices=self.widgets.keys(),
            labels=(self.widgets[widget].title for widget in self.widgets),
            label='Display Image'
        ).widget()
        image_choice = QtWidgets.QHBoxLayout()
        image_choice.addWidget(widgets['label'])
        image_choice.addWidget(widgets['widget'])
        value_load = QtWidgets.QHBoxLayout()
        value_load.addWidget(QtWidgets.QPushButton('Load...'))
        value_load.addWidget(QtWidgets.QPushButton('Save...'))
        boxbox = QtWidgets.QVBoxLayout()
        boxbox.addLayout(image_choice)
        boxbox.addLayout(value_load)
        box.setLayout(boxbox)
        output_control = QtWidgets.QGridLayout()
        output_box = QtWidgets.QGroupBox('Outputs')
        output_box.setLayout(output_control)
        output_control.addWidget(QtWidgets.QPushButton('CSV output'))
        output_control.addWidget(QtWidgets.QPushButton('CSV output'), 1, 0)
        layout.addWidget(box)
        self.image_choice = widgets['widget']
        self.image_choice.valueChanged.connect(self.display)

    def display(self):
        """Changes displays or something, idk"""
        self.view = self._outputs[self.image_choice.value()]
        self.view_changed.emit()

    def create_methods(self):
        """Constructs methods for this method"""
        for method in self.methods:
            self.methods[method] = self.methods[method]()

    def connect_methods(self):
        """Connects the methods for this function stack"""
        for edge in self.method_graph:
            # Special names: IMAGE, DATA, INPUT
            end = self.method_graph[edge]
            print("{} → {}".format(end, edge))
            if edge == 'output_image':
                # Output image is mapped to this guy's output
                self.output_image = self.methods[end].output_image
            elif edge == 'output_data':
                self.output_data = self.methods[end].output_data
            elif end == 'input_image':
                # Input image is mapped to this guy's input
                self.input_image = self.methods[edge].input_image
            else:
                # Other edges are mapped between edges
                connection_end = self.methods[edge].input_image
                connection_start = self.methods[end].output_image
                #print('{} → {}'.format(connection_end, connection_start))
                connection_end.source = connection_start
            if edge.startswith('output'):
                getattr(self.methods[end], edge).changed.connect(self.output_changed.emit)

            # Connection is made
            #print('{} → {}'.format(connection_start, connection_end))

    @property
    def values(self) -> dict:
        """Values provided by subservient functions"""
        return {
            function: self.widgets[function].values
            for function in self.widgets
        }

class ShortStack(BaseStack):
    """A short stack that does not output data, but only images"""
    methods = {
        'gaussian_blur': functions.GaussianBlur,
        'adaptive_threshold': functions.AdaptiveThreshold,
        'morphology': functions.Morphology,
    }
    method_graph = {
        'output_image': 'morphology',
        'morphology': 'adaptive_threshold',
        'adaptive_threshold': 'gaussian_blur',
        'gaussian_blur': 'input_image',
    }

class ThresholdStack(BaseStack):
    """A function stack for adaptive thresholds"""
    # List of functions that this class has
    methods = {
        'gaussian_blur': functions.GaussianBlur,
        'adaptive_threshold': functions.AdaptiveThreshold,
        'morphology': functions.Morphology,
        'contour_extract': functions.Contours,
        'size_filter': functions.SizeFilter,
        'draw_contours': functions.DrawContours,
    }
    # Description of the dependency tree.
    # Disappointingly, this actually needs to be a graph, because otherwise we
    # can't figure out what goes where for non-monadic functions.
    # method_graph describes how the signal's and slots from the different
    # functions are connected.
    method_graph = {
        'IMAGE': 'draw_contours',
        'DATA': 'size_filter',
        'draw_contours': ('INPUT', 'size_filter'),
        'size_filter': 'contour_extract',
        'contour_extract': 'morphology',
        'morphology': 'adaptive_threshold',
        'adaptive_threshold': 'gaussian_blur',
        'gaussian_blur': 'INPUT'
    }

class NullStack(BaseStack):
    """A stack that does nothing.

    No really, nothing is implemented here.
    """
