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

import logging
import csv

from PyQt5 import QtWidgets, QtCore

import cv2

from .video import Video
from . import functions
#from .functions import params

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
            self.widgets[key].values = value

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

    def __init__(self, *args, in_file=None, csv_file=None, vid_file=None, **kwargs):
        super().__init__(*args, **kwargs)
        # These two are no longer properties, as they don't need anything to
        # happen on setting or loading.
        self.video = None
        self.files = {'in': in_file, 'csv': csv_file, 'vid': vid_file}
        self.csv_file = csv_file
        self.vid_file = vid_file
        self._running = False
        self._enabled = False
        self._view = None
        self.csv_writer = None
        self.csv_connection = None
        self.video_output = None
        self.create_methods()
        self.connect_methods()
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
        if in_file is None:
            self._in_file = None
        else:
            self.in_file = in_file

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
            # Special names: IMAGE, DATA, INPUT
            if end == 'output_image':
                # Output image is mapped to this guy's output
                logging.info('Special `%s` from `%s` mapped to `%s`', end, start, self)
                self.output_image = self.methods[start].output_image
            elif end == 'output_data':
                logging.info('Special `%s` from `%s` mapped to `%s`', end, start, self)
                self.output_data = self.methods[start].output_data
            elif start == 'input_image':
                # Input image is mapped to this guy's input
                logging.info('Special `%s` from `%s` mapped to `%s`', end, start, self)
                self.input_image = self.methods[end].input_image
            elif start == 'input_data':
                logging.info('Special `%s` from `%s` mapped to `%s`', end, start, self)
                self.input_data = self.methods[end].input_data
            else:
                # Other edges are mapped between edges
                start_set = {method.split('_')[-1] for method in self.methods[start].outputs.keys()}
                end_set = {method.split('_')[-1] for method in self.methods[end].inputs.keys()}
                ## What to connect
                conn_type = start_set.intersection(end_set)
                logging.info('There are %i connections possible.', len(conn_type))
                for connection in conn_type:
                    connection_start = getattr(self.methods[start], f'output_{connection}')
                    connection_end = getattr(self.methods[end], f'input_{connection}')
                    connection_end.source = connection_start
                    logging.info('Internal `%s` from `%s` mapped to `%s`',
                                 connection, self.methods[start], self.methods[end])
            if end.startswith('output'):
                getattr(self.methods[start], end).changed.connect(self.output_changed.emit)

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
        }
        widget = StackWidget(widgets)
        widget.view_changed.connect(self.set_view)
        self.values = widget.values
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
        return self.files['in']
    @in_file.setter
    def in_file(self, value: str):
        self.files['in'] = value
        if value is not None:
            self.video = Video(value)
            self.input_image.data = self.video.frame
        # This might cause problems, depending on what the behaviour of the
        # video object was.

    @property
    def pos(self) -> int:
        """Position in the video file"""
        return self.video.position
    @pos.setter
    def pos(self, value: int):
        if value != self.pos:
            self.video.position = value
            self.fetch_image()

    @property
    def running(self) -> bool:
        """The running state. True indicates a segmentation is running"""
        return self._running
    @running.setter
    def running(self, value: bool):
        self._running = value
        if value:
            self.in_file = self.in_file
            self.output_image.changed.connect(self.segment)
            if self.csv_file is not None:
                self.create_csv_writer()
            if self.vid_file is not None:
                self.create_vid_writer()
            self.next()
        else:
            self.output_image.changed.disconnect(self.segment)
            self.destroy_csv_writer()
            self.destroy_vid_writer()

    def create_csv_writer(self):
        """Opens the file at csv_file and starts a dictwriter. Connects output_data"""
        self.csv_connection = open(self.csv_file, 'w')
        self.csv_writer = csv.DictWriter(self.csv_connection, fieldnames=self.output_data.fields)
        self.csv_writer.writeheader()
        self.output_data.changed.connect(self.write_csv)
        logging.debug('Created CSV writer %s at %s', self.csv_writer, self.csv_connection)

    def destroy_csv_writer(self):
        """Removes the csv writer"""
        if self.csv_file is not None:
            self.output_data.changed.disconnect(self.write_csv)
            self.csv_connection.close()
            logging.debug('CSV output destroyed')

    def write_csv(self):
        """Writes current output_data row to the csv file"""
        for row in self.output_data.data:
            self.csv_writer.writerow(row)
            logging.debug('Wrote to csv: %s', row)

    def create_vid_writer(self):
        """Opens the ifle at vid_file and starts a video thing"""
        self.video_output = cv2.VideoWriter(self.vid_file,
                                            cv2.VideoWriter_fourcc(*self.video.fourcc),
                                            self.video.framerate, self.video.resolution)
        logging.debug('Created video writer %s at %s', self.video_output, self.vid_file)
        self.output_image.changed.connect(self.write_vid)

    def write_vid(self):
        """Writes the current output_image to the video file

        Todo: Make videos a separate function
        """
        self.video_output.write(self.output_image.data)
        logging.debug('Wrote video frame')

    def destroy_vid_writer(self):
        """Closes the video writer"""
        if self.vid_file:
            self.video_output.release()
            self.output_image.changed.disconnect(self.write_vid)
            logging.debug('Video output destroyed')

    def segment(self):
        """Segments. If StopIteration is encountered, stops"""
        logging.debug('Load frame %i', self.video.position)
        try:
            self.next()
        except StopIteration:
            self.complete.emit()
            self.in_file = self.in_file
            # Seems effectless, but isn't.
            # Actually resets the video device

    @QtCore.pyqtSlot(int)
    def set_pos(self, index: int):
        """Sets position of video to index"""
        print(self.sender())
        self.pos = index

    def next(self):
        """Loads next image from video device"""
        self.input_image.data = next(self.video)
        self.pos_changed.emit(self.pos)

    def fetch_image(self):
        """Fetches current frame from video object"""
        self.input_image.data = self.video.frame

    @property
    def outputs(self):
        """Output of all variables here"""
        return {output: self._outputs[output].data for output in self._outputs}

    @property
    def values(self) -> dict:
        """Values provided by subservient functions"""
        return {
            function: self.methods[function].values
            for function in self.methods
        }
    @values.setter
    def values(self, value: dict):
        for method in self.methods:
            self.methods[method].values = value[method]

    def set_values(self, value: dict):
        """Sets values attribute"""
        self.values = value

    def run(self):
        """Runs this thread"""
        logging.info('%s Started', type(self).__name__)
        self.exec_()
        logging.info('%s Finished', type(self).__name__)

class ShortStack(BaseStack):
    """A short stack that does not output data, but only images"""
    methods = {
        #'input_image': functions.special.InputImage,
        'gaussian_blur': functions.GaussianBlur,
        'adaptive_threshold': functions.AdaptiveThreshold,
        'morphology': functions.Morphology,
        'bgr2gray': functions.BGR2Gray,
        #'output_image': functions.special.OutputImage,
        #'output_data': functions.special.OutputData,
    }
    method_graph = {
        'output_image': 'morphology',
        'morphology': 'adaptive_threshold',
        'adaptive_threshold': 'gaussian_blur',
        'gaussian_blur': 'bgr2gray',
        'bgr2gray': 'input_image',
    }

class ThresholdStack(BaseStack):
    """A function stack for adaptive thresholds"""
    # List of functions that this class has
    methods = {
        'bgr2gray': functions.BGR2Gray,
        'gaussian_blur': functions.GaussianBlur,
        'adaptive_threshold': functions.AdaptiveThreshold,
        'morphology': functions.Morphology,
        'contour_extract': functions.Contours,
        'size_filter': functions.SizeFilter,
        'draw_contours': functions.DrawContours,
        'feature_extraction': functions.ExtractPolygonFeatures
    }
    # Description of the dependency tree.
    # Disappointingly, this actually needs to be a graph, because otherwise we
    # can't figure out what goes where for non-monadic functions.
    # method_graph describes how the signal's and slots from the different
    # functions are connected.
    method_graph = {
        'output_image': 'draw_contours',
        'output_data': 'feature_extraction',
        'feature_extraction': 'size_filter',
        'draw_contours': ('bgr2gray', 'size_filter'),
        'size_filter': 'contour_extract',
        'contour_extract': 'morphology',
        'morphology': 'adaptive_threshold',
        'adaptive_threshold': 'gaussian_blur',
        'gaussian_blur': 'bgr2gray',
        'bgr2gray': 'input_image',
    }

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
