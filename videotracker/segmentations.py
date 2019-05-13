"""Various segmentation methods"""

import json
import csv

from types import MethodType
from pprint import pprint

from typing import Callable
from dataclasses import dataclass

from PyQt5.QtWidgets import (QWidget, QSpinBox, QPushButton,
                             QComboBox, QFileDialog, QGridLayout, QLabel,
                             QDoubleSpinBox)

from PyQt5.QtCore import QThread, pyqtSignal

import cv2

from .video import Video
from . import contours

@dataclass
class BaseParam:
    """Parameter base"""
    label: str = ''
    widget_callable: Callable = QWidget

    def widget(self):
        """Returns a widget  dictionary: A dict with 'label' and 'widget'"""
        members = self.__dict__
        construct = {
            member: members[member] for member in members
            if not member.startswith('__')
            and member not in ('label', 'widget_callable')
        }
        return {
            'widget': self.widget_callable(**construct),
            'label': QLabel(self.label),
        }

@dataclass
class IntParam(BaseParam):
    """Integer Parameter"""
    widget_callable: Callable = QSpinBox
    minimum: int = 0
    maximum: int = 100
    value: int = minimum
    singleStep: int = 1

@dataclass
class FloatParam:
    """Integer Parameter"""
    widget_callable: Callable = QDoubleSpinBox
    label: str = ''
    minimum: float = 0
    maximum: float = 100
    singleStep: float = 1

@dataclass
class ChoiceParam:
    """Choice Parameter"""
    label: str = ''
    choices: tuple = tuple()
    labels: tuple = tuple()

    def widget(self):
        """Creates a widget dictionary"""
        dictionary = {'label': QLabel(self.label)}
        widget = dictionary['widget'] = QComboBox()
        for label, choice in zip(self.labels, self.choices):
            widget.addItem(label, choice)
        widget.valueChanged = widget.currentIndexChanged
        # setValue for QComboBox
        def set_data(self, data=None):
            """Method for setting the data of the QComboBox"""
            print(self)
            self.setCurrentIndex(self.findData(data))
        widget.setValue = MethodType(set_data, widget)
        widget.value = widget.currentData
        return dictionary

class SegmentationThread(QThread):
    """A thread for segmentations

    This also contains the Video.
    """
    # Apparently Qt5 does not like you mixing QThread with QWidget.

    # Signal emitted when a new frame is loaded
    frame_changed = pyqtSignal(int)
    # Signal emitted when a new result was computed
    results_changed = pyqtSignal(int)
    # Signal to indicate that the loop has run out of frames.
    loop_complete = pyqtSignal(bool)
    computing = pyqtSignal(bool)

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

class BaseSegmentation(QWidget):
    #pylint: disable=abstract-method
    # This class is also abstract
    """Abstract segmentation"""

    params = {}

    values_changed = pyqtSignal(dict)
    frame_changed = pyqtSignal(int)
    results_changed = pyqtSignal(int)

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
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        for row, widget in enumerate(self.widgets):
            self.layout.addWidget(self.widgets[widget]['widget'], row, 0)
            self.layout.addWidget(self.widgets[widget]['label'], row, 1)
        self.load_button = QPushButton('Load...', pressed=self.load_values)
        self.layout.addWidget(self.load_button)
        self.layout.addWidget(QPushButton('Save...', pressed=self.save_values))
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
        file_name = QFileDialog.getOpenFileName(self, 'Load values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.load(file_name[0])

    def save_values(self):
        """Spawns a file picker dialog to save values"""
        file_name = QFileDialog.getSaveFileName(self, 'Save values', self.value_file, '*.json')
        if file_name[0]:
            self.value_file = file_name[0]
            self.save(file_name[0])

class ThresholdSegmentation(BaseSegmentation):
    """Sample segmentation"""
    params = {
        'blur': IntParam(singleStep=2, minimum=1, maximum=100, label='Blur'),
        'thresh_type': ChoiceParam(
            choices=(cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C),
            labels=('Mean', 'Gaussian'),
            label='Threshold Type',
        ),
        'size': IntParam(singleStep=2, minimum=3, maximum=100, label='Block Size'),
        'c_value': IntParam(singleStep=1, minimum=-100, maximum=100, label='C Value'),
        'kernel_size': IntParam(singleStep=2, minimum=1, maximum=100, label='Kernel Size'),
        'min_size': IntParam(singleStep=1, maximum=1000, label='Minimum Size'),
        'max_size': IntParam(singleStep=1, maximum=1000, value=1000, label='Maximum Size'),
    }
    def function(self, img, thresh_type, blur, size, c_value, kernel_size, min_size, max_size):
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
