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

import json
import csv

from PyQt5 import QtWidgets, QtCore
import cv2

from .video import Video
from . import contours
from . import functions
from .functions import params

class SegmentationThread(QtCore.QThread):
    """A thread for segmentations

    This also contains the Video.
    """
    # Apparently Qt5 does not like you mixing QThread with QWidget.

    # Signal emitted when a new frame is loaded
    frame_changed = QtCore.pyqtSignal(int)
    # Signal emitted when a new result was computed
    results_changed = QtCore.pyqtSignal(int)
    # Signal to indicate that the loop has run out of frames.
    loop_complete = QtCore.pyqtSignal(bool)
    computing = QtCore.pyqtSignal(bool)

    @property
    def options(self) -> dict:
        """Options that will be used to compute images.

        Setting this value changes the boolean self.options_changed to True.
        """
        return self._options
    @options.setter
    def options(self, value: dict):
        self._options = value
        self.options_changed = True

    def set_options(self, value):
        """Slot for a signal to set the options of this thing"""
        self.options = value

    @property
    def input_file(self) -> str:
        """This value is the input video that is used.

        Setting his value changes input_changed to be set to True.
        This parameter cannot set the video object itself, as that causes
        issues with OpenCV.
        """
        return self._input_file
    @input_file.setter
    def input_file(self, value: str):
        self._input_file = value
        self.input_changed = True
        print('input_file: {}, change {}'.format(self._input_file, self.input_changed))

    @property
    def position(self) -> int:
        """This value stores the position that we have to compute"""
        return self._position
    @position.setter
    def position(self, value: int):
        self._position = value
        self.position_changed = True

    def __init__(self, *args, video=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Loop control bits:
        self.started = False # Has the thread been started or killed
        self.running = False # Is the thread running for a whole video.
        # video is a parameter that holds the video capture device
        self.video = None
        self.draw = True
        # These are the input files
        self._input_file = video
        self.input_changed = False
        # These are the options that are set by the parents and are passed to self.function
        self._options = {}
        self.options_changed = False
        self._position = 0
        self.position_changed = False
        # Various output files.
        self.csv_file = None
        self.vid_file = None
        # Result is the parameter than can be grabbed by other things when we
        # emit a signal on results_changed.
        # self.frame stores the raw frame.
        # self.result stores the image with annotations
        # self.contours stores contours
        self.result = None
        self.frame = None
        self.contours = None

    def set_video(self, file_name):
        """Sets the input_file variable. This is mostly meant as a slot for signals"""
        self.input_file = file_name

    def set_position(self, position: int):
        """Sets the video position. Used as a slot for signals from beyond"""
        self.position = position

    def stop(self):
        """Stops the loop from the start/stop bit"""
        self.started = False

    def draw_contours(self):
        """Draw contours if self.draw is set

        self.draw exists to make high polycount computations quicker, as then
        the things won't have to be drawn if set to False.
        """
        if self.draw:
            copy = self.frame.copy()
            self.result = cv2.drawContours(copy, self.contours, -1, (0, 0, 255), 3)

    def full_loop(self):
        """Full loop.

        This method starts the full loop, and exits once all frames have been processed
        """
        print('loop, reopen video')
        self.video.close()
        self.video = Video(self.input_file)
        if self.csv_file:
            print('Writing csv: {}'.format(self.csv_file))
            connection = open(self.csv_file, 'w')
            csv_writer = csv.DictWriter(connection, fieldnames=contours.FEATURES)
            csv_writer.writeheader()
        if self.vid_file:
            print('Writing video: {}'.format(self.vid_file))
            fourcc = cv2.VideoWriter_fourcc(*self.video.fourcc)
            out = cv2.VideoWriter(self.vid_file, fourcc,
                                  self.video.framerate, self.video.resolution)
        for frame in self.video:
            self.frame = frame
            self.frame_changed.emit(self.video.position)
            self.contours = self.function(frame, **self.options)
            output = contours.extract_features(self.contours)
            self.result = cv2.drawContours(frame, self.contours, -1, (0, 0, 255), 3)
            self.draw_contours()
            self.results_changed.emit(self.position)
            # How many objects did we find, and current frame status
            print('[{:>5}/{:>5}] {}'.format(self.video.position,
                                            self.video.frames, len(output)))
            # CSV output section
            if self.csv_file:
                for row in output:
                    row.update({'timestamp': self.video.time, 'frame': self.video.position})
                    csv_writer.writerow(row)
            if self.vid_file:
                out.write(self.result)
            if not self.running:
                break
        if self.csv_file:
            connection.close()
        if self.vid_file:
            out.release()
        self.loop_complete.emit(True)

    def single(self):
        """Run to compute a single image"""
        if self.position_changed or self.frame is None:
            # If we changed the position, or have no self.frame, we get a frame.
            self.computing.emit(True)
            print('position changed')
            self.video.position = self.position
            print('Video {}'.format(self.input_file))
            self.frame = self.video.grab(self.position)
            self.frame_changed.emit(self.video.position)
            print('regrab complete')
            self.computing.emit(False)
        if self.options_changed or self.position_changed:
            # Values have been changed, we will thus run this bit.
            self.computing.emit(True)
            print('options changed')
            self.contours = self.function(self.frame, **self.options)
            self.draw_contours()
            self.results_changed.emit(self.position)
            self.options_changed = False
            self.computing.emit(False)
            print('recompute complete')
        if self.position_changed:
            self.position_changed = False

    def event_loop(self):
        """The loop that the background thread goes through"""
        while self.started:
            # First we check for a change in videos.
            # If the video was changed, a new video will be loaded.
            if self.input_changed:
                print('load new video')
                if self.video is not None:
                    self.video.close()
                self.video = Video(self.input_file)
                print('position: {}'.format(self.video.position))
                self.input_changed = False
            # This is what will happen here: if the running flag has been set
            # (i.e. by hitting the run button), the full loop will be exectued
            # (run through all of the bits) If it hasn't been set, we will
            # recompute the current image.
            if self.running:
                self.full_loop()
            else:
                self.single()
            if not self.started:
                # We can also break before the sleep.
                break
            self.msleep(100)

    def run(self):
        """Running, loads the video and then calls self.event_loop()"""
        self.started = True
        if self.input_file is None:
            raise ValueError('video file is not defined')
        self.video = Video(self.input_file)
        self.event_loop()
        self.video.close()

    def function(self, *args, **kwargs):
        """Function that defines the segmentation"""
        raise NotImplementedError

class BaseSegmentation(QtWidgets.QWidget):
    #pylint: disable=abstract-method
    # This class is also abstract
    """Abstract segmentation"""

    params = {}

    values_changed = QtCore.pyqtSignal(dict)
    frame_changed = QtCore.pyqtSignal(int)
    results_changed = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enabled = True
        self.values = {}
        self.options = {}
        self.value_file = ""
        self.thread = SegmentationThread()
        self.thread.frame_changed.connect(self.frame_changed)
        self.thread.results_changed.connect(self.results_changed)
        self.thread.function = self.function
        self.frame = self.thread.frame
        self.result = self.thread.result
        self.create_widgets()
        self.create_gui()

    def start(self, *args, **kwargs):
        """Starts the thread"""
        self.thread.options = self.values
        self.thread.start(*args, **kwargs)

    def create_widgets(self):
        """Creates the widgets from self.params"""
        self.widgets = {param: self.params[param].widget() for param in self.params}

    def create_gui(self):
        """Creates main gui elements"""
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        for row, widget in enumerate(self.widgets):
            self.layout.addWidget(self.widgets[widget]['widget'], row, 0)
            self.layout.addWidget(self.widgets[widget]['label'], row, 1)
        self.load_button = QtWidgets.QPushButton('Load...', pressed=self.load_values)
        self.layout.addWidget(self.load_button)
        self.layout.addWidget(QtWidgets.QPushButton('Save...', pressed=self.save_values))
        for widget in self.widgets:
            self.widgets[widget]['widget'].valueChanged.connect(self.emit_values)

    def emit_values(self):
        """Emits the values in the values_changed signal"""
        self.values_changed.emit(self.values)

    def compute(self, frame):
        """Computes the current result of the segmentation"""
        return self.function(frame, **self.values)

    @property
    def enabled(self) -> bool:
        """Enabledness of the option widgets"""
        return self._enabled
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        self.load_button.setEnabled(value)
        for widget in self.widgets:
            self.widgets[widget]['widget'].setEnabled(value)

    @property
    def values(self) -> dict:
        """Values configured in the segmentation method"""
        return {
            name: self.widgets[name]['widget'].value()
            for name in self.widgets
        }
    @values.setter
    def values(self, values: dict):
        for value in values:
            if value in self.widgets:
                self.widgets[value]['widget'].setValue(values[value])

    def load(self, file_name: str):
        """Loads a file of value"""
        with open(file_name, 'r') as conn:
            values = json.load(conn)
        print(values)
        self.values = values

    def save(self, file_name: str):
        """Loads a file of value"""
        with open(file_name, 'w') as conn:
            json.dump(self.values, conn)

    def load_values(self):
        """Spawns a file picker dialog to load values"""
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Load values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.load(file_name[0])

    def save_values(self):
        """Spawns a file picker dialog to save values"""
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.save(file_name[0])

class ThresholdSegmentation(BaseSegmentation):
    """Sample segmentation"""
    params = {
        'blur': params.IntParam(singleStep=2, minimum=1, maximum=100, label='Blur'),
        'thresh_type': params.ChoiceParam(
            choices=(cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C),
            labels=('Mean', 'Gaussian'),
            label='Threshold Type',
        ),
        'size': params.IntParam(singleStep=2, minimum=3, maximum=100, label='Block Size'),
        'c_value': params.IntParam(singleStep=1, minimum=-100, maximum=100, label='C Value'),
        'kernel_size': params.IntParam(singleStep=2, minimum=1, maximum=100, label='Kernel Size'),
        'min_size': params.IntParam(singleStep=1, maximum=1000, label='Minimum Size'),
        'max_size': params.IntParam(singleStep=1, maximum=1000, value=1000, label='Maximum Size'),
    }
    def function(self, img, thresh_type, blur, size, c_value, kernel_size, min_size, max_size, colour):
        """Adaptive threshold segmentation of image

        Takes an image img
        Returns polygons
        """
        # pylint: disable=too-many-arguments,no-self-use, arguments-differ
        # pylint: disable=redefined-outer-name
        # I need this many arguments, and I can't have this as not a method.
        # Additionally, this method can't have a predefined set of parameters.
        frame = img.copy()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (blur, blur), 0)
        frame = cv2.adaptiveThreshold(frame, 255, thresh_type,
                                      cv2.THRESH_BINARY_INV, size, c_value)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        frame = cv2.morphologyEx(frame, cv2.MORPH_OPEN, kernel)
        contours = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = [contour for contour in contours
                    if min_size < cv2.contourArea(contour) < max_size]
        return contours

class BaseStack(QtWidgets.QWidget):
    """An abstract stack of function"""
    valueChanged = QtCore.pyqtSignal(dict) # The values of the widgets have changed
    output_changed = QtCore.pyqtSignal(int)  # Computational output(s) have changed
    view_changed = QtCore.pyqtSignal() # The chosen view has changed.

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

    @property
    def input_file(self) -> str:
        """The input file"""
        return self._input_file
    @input_file.setter
    def input_file(self, value: str):
        # pylint: disable=attribute-defined-outside-init
        # Dear pylint, this is implicit. Yours truly, me.
        self._input_file = value
        if value is not None:
            self.video = Video(value)
            self.load_frame()
        # This might cause problems, depending on what the behaviour of the
        # video object was.

    @property
    def pos(self) -> int:
        return self.video.position
    @pos.setter
    def pos(self, value: int):
        self.video.position = value
        self.load_frame()

    def load_frame(self):
        """Loads current frame"""
        self.input_image.data = self.video.frame
        import ipdb; ipdb.set_trace()  # XXX BREAKPOINT


    def __init__(self, *args, input_file=None, csv_file=None, vid_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        # These two are no longer properties, as they don't need anything to
        # happen on setting or loading.
        self.video = None
        self.csv_file: str = csv_file
        self.vid_file: str = vid_file
        self.input_file: str = input_file
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
