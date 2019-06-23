"""Widgets of the video-tracker"""

import logging
import os

from PyQt5.QtWidgets import (QWidget, QMainWindow, QAction, #QMessageBox,
                             QFileDialog, qApp, QCheckBox, QPushButton,
                             QGridLayout, QDockWidget, QVBoxLayout, QBoxLayout,
                             QLabel, QSizePolicy, QScrollArea, QSlider,
                             QHBoxLayout, QSpinBox, QColorDialog)

from PyQt5 import QtWidgets, QtCore, QtGui

import cv2

from . import helpers

class BaseFileObject:
    """A base widget for videotracker objects

    Provides several things:
        - csv property for csv files
        - vid proprety for video files
        - input property for input files
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.files = {
            'in': None,
            'csv': None,
            'vid': None,
            'config': None,
        }
        self.widgets = {}

    @property
    def in_file(self) -> str:
        """Input file

        None indicates no file, a string is a file handle.
        """
        return self.files['in']
    @in_file.setter
    def in_file(self, value: str):
        self.files['in'] = value
        for widget in self.widgets:
            try:
                self.widgets[widget].in_file = value
            except AttributeError:
                pass

    @property
    def csv_file(self) -> str:
        """CSV output file

        None indicates no file, a string is a file handle.
        """
        return self.files['csv']
    @csv_file.setter
    def csv_file(self, value: str):
        self.files['csv'] = value
        for widget in self.widgets:
            try:
                self.widgets[widget].csv_file = value
            except AttributeError:
                pass

    @property
    def vid_file(self) -> str:
        """Video output file

        None indicates no file, a string is a file handle.
        """
        return self.files['vid']
    @vid_file.setter
    def vid_file(self, value: str):
        self.files['vid'] = value
        for widget in self.widgets:
            try:
                self.widgets[widget].vid_file = value
            except AttributeError:
                pass
class ColorButton(QPushButton):
    """A button, that when pushed, returns a colour"""

    valueChanged = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._color = QtGui.QColor()
        self.dialog = QColorDialog()
        self.clicked.connect(self.pick_color)
        self.setStyleSheet("color: {}".format(self.value()))
        self.setText(self.value())

    def setValue(self, value: str):
        """Sets the button colour value"""
        # pylint: disable=invalid-name
        # Unfortunately, Qt5 naming is awful.
        self._color = QtGui.QColor(value)
        self.valueChanged.emit(self.value())
        self.setStyleSheet("color: {}".format(self.value()))
        self.setText(self.value())

    def value(self) -> str:
        """The value of the widget"""
        return self._color.name()

    def pick_color(self):
        """Pick the colour using the dialog"""
        self._color = self.dialog.getColor(self._color)
        self.setValue(self._color.name())

class FancyScrollArea(QScrollArea):
    """A better QScrollArea"""
    def wheelEvent(self, event):
        """Wheel events overloaded to allow zooming and sideways scrolls"""
        # pylint: disable=invalid-name
        # x is snek_case, just a very very short snek.
        delta_y = event.angleDelta().y()
        delta_x = event.angleDelta().x()
        x = self.horizontalScrollBar().value()
        y = self.verticalScrollBar().value()
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            # Zoom, but for this it means doing nothing.
            pass
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            # Flipped
            self.verticalScrollBar().setValue(y-delta_x)
            self.horizontalScrollBar().setValue(x-delta_y)
        else:
            # Ordinary
            self.verticalScrollBar().setValue(y-delta_y)
            self.horizontalScrollBar().setValue(x-delta_x)

class ImageView(QWidget):
    """The view area.

    The view area consists of a label with a pixmap in a scrollarea
    GUI consists of a QVBox with:
        - QScrollArea with QLabel
        - QHBox:
            QLabel, QSlider, QSpinBox

    By setting image it is possible to display an image in the QScrollArea.
    The scrollarea can be zoomed by setting the local property scale. The
    position of the slider, and maximum possible position of the slider can
    be set with the pos and pos_max properties.
    """
    # Pylint says there is too many instance attributes.
    # I disagree however. This is in part due to the usage of setters and
    # getters with private attributes. There is 6 user-facing attributes in
    # total and that is very managable.
    # pylint: disable=too-many-instance-attributes

    pos_changed = QtCore.pyqtSignal(int)
    # Frame that we have changed to

    @property
    def scale(self):
        """The scale of the image

        Internally stored in _scale. Setting this variable will resize the image
        to the desired scale.
        """
        return self._scale
    @scale.setter
    def scale(self, value):
        # pylint: disable=attribute-defined-outside-init
        self._scale = value
        if self.image_lab.pixmap():
            self.image_lab.resize(self.scale * self.image_lab.pixmap().size())

    @property
    def image(self):
        """The image displayed, as a numpy array.

        Setting this variable causes:
            - An image to be converted to a QtGui.QImage and then displayed in the
              ScrollArea
            - Spinboxes, Sliders to be enabled
            - If this is the first image to be loaded, scale set to 1.0

        The numpy array is stored in self.frame
        """
        return self.frame
    @image.setter
    def image(self, frame):
        first = self.frame is None
        try:
            dim = frame.ndim
        except AttributeError:
            dim = None
        if dim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        self.frame = frame
        height, width, channels = frame.shape
        bytes_per_line = channels*width
        qimg = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        self.image_lab.setPixmap(QtGui.QPixmap.fromImage(qimg))
        if first:
            self.scale = 1.0
        else:
            self.scale = self.scale

    @property
    def pos_max(self):
        """The maximum position possible

        Setting this variable will change the lower part of the label and the
        maximum values of slider and spinbox.
        """
        return self._pos_max
    @pos_max.setter
    def pos_max(self, value):
        # Attribute _pos_max actually gets defined in init, pylint is confused
        # by @property's setter
        # pylint: disable=attribute-defined-outside-init
        self._pos_max = value
        self.slidelabel.setText(self.lab_text_template.format(self.pos, value))
        self.sbox.setMaximum(value)
        self.slider.setMaximum(value)

    @property
    def pos(self):
        """Position of the slider and video

        Setting this will: change the slider, label and spinbox.
        NB: As MainView connects to slider's valueChanged, setting this will
        indirectly cause effects in MainView.
        """
        return self.slider.value()
    @pos.setter
    def pos(self, value):
        self.slider.setValue(value)
        self.sbox.setValue(value)
        self.slidelabel.setText(self.lab_text_template.format(value, self.pos_max))
        self.pos_changed.emit(value)

    def set_pos(self, value: int):
        """Sets the position. Used as a slot for other widgets"""
        self.pos = value

    @property
    def enabled(self) -> bool:
        """State of the controls"""
        return self._enabled
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        self.slider.setEnabled(value)
        self.sbox.setEnabled(value)

    @property
    def source(self):
        """Source image to copy on get call"""
        return self._source
    @source.setter
    def source(self, value):
        try:
            self._source.view_changed.disconnect(self.get)
        except TypeError:
            pass
        except AttributeError:
            pass
        self._source = value
        self._source.view_changed.connect(self.get)

    def get(self):
        """Gets new data"""
        self.image = self.source.view.data
        logging.debug('Data copied to ImageView')

    def __init__(self):
        super().__init__()
        self.lab_text_template = '{:}/{:}'
        self.create_gui()
        self.pos_max = 0
        self.frame = None
        self._enabled = False
        self._source = None

    def wheelEvent(self, event):
        """Overload the wheelevent"""
        if event.modifiers() == QtCore.Qt.ShiftModifier:
            # Zooms
            portion = (event.angleDelta().y() / 8 / 360) + 1
            self.scale *= portion

    def create_gui(self):
        """Creates the image view gui

        GUI consists of a QVBox with:
            - QScrollArea with QLabel
            - QHBox:
                QLabel, QSlider, QSpinBox

        The bottom QHBox is an indicator and control area for the frame to be
        displayed. It could be any other value though. What it does depends on
        what signals are connected.
        Internally all Widgets in the HBox are linked.
        """
        self.image_lab = QLabel()
        self.image_lab.setBackgroundRole(QtGui.QPalette.Dark)
        self.image_lab.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_lab.setScaledContents(True)
        self.scrollarea = FancyScrollArea()
        self.scrollarea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollarea.setWidget(self.image_lab)
        self.scrollarea.installEventFilter(self)
        self.slidelabel = QLabel(self.lab_text_template.format(0, 0))
        self.slider = QSlider(QtCore.Qt.Horizontal, enabled=False,
                              minimum=0, maximum=0, sliderMoved=lambda x: setattr(self, 'pos', x),
                              valueChanged=lambda x: setattr(self, 'pos', x))
        self.sbox = QSpinBox(maximum=0, enabled=False,
                             valueChanged=lambda x: setattr(self, 'pos', x))
        # Missing: new value causing a signal to be sent.
        slidebox = QHBoxLayout()
        slidebox.addWidget(self.slidelabel)
        slidebox.addWidget(self.slider)
        slidebox.addWidget(self.sbox)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.scrollarea)
        self.layout.addLayout(slidebox)
        self.setLayout(self.layout)
        self.setMinimumSize(512, 512)

    def reset(self):
        """Reset the widget.

        This is used to avoid issues caused by loading a video with a different
        maximum frame count
        """
        self.slider.blockSignals(True)
        self.pos_max = 0
        self.pos = 0
        self.slider.blockSignals(False)

    def zoom_in(self):
        """Zooms in (+25%)"""
        self.scale *= 1.25

    def zoom_out(self):
        """Zooms out (-25%)"""
        self.scale *= 0.8

    def zoom_optimal(self):
        """Zooms to optimal extent

        Optimal scale is calculated by:

            should/current * self.scale

        for both width and height, the minimum of which is taken as the new scale.
        """
        current_width = self.image_lab.width()
        should_width = self.scrollarea.width()
        current_height = self.image_lab.height()
        should_height = self.scrollarea.height()
        self.scale = min(should_width/current_width * self.scale,
                         should_height/current_height * self.scale)

class SideDock(QDockWidget, BaseFileObject):
    """Sidebar dock area

    Consists of an upper custom widget (defined by custom in construction) and a
    lower constant widget. The lower widget adjust various output file
    properties, and offers controls for starting/stopping.
    """
    # To my count there is seven-ish properly public attributes.
    # A further seven attributes define various UI elements which need to be
    # accessed frequently by property setters and getters.
    # As such I don't think there is much room for improvement
    # pylint: disable=too-many-instance-attributes

    started = QtCore.pyqtSignal(bool)

    @property
    def csv_file(self) -> str:
        """CSV output. Either string or None.

        None indicates that no output shall be made, string indicates a file
        handle to which output shall be made.
        Setting this set the checkbox to the appropriate value and
        enables/disables the csv_button.
        The checkbox will not emit signals for that change.
        """
        return self.files['csv'] if self.csv_cbox.checkState() else None
    @csv_file.setter
    def csv_file(self, value: str):
        self.csv_cbox.blockSignals(True)
        self.module.csv_file = value
        if value is not None:
            self.csv_cbox.setCheckState(2)
            self.files['csv'] = value
        else:
            self.csv_cbox.setCheckState(0)
        self.csv_button.setEnabled(value is not None)
        self.csv_cbox.blockSignals(False)

    @property
    def vid_file(self) -> str:
        """Boolean indicating vid output

        None indicates that no output shall be made, string indicates a file
        handle to which output shall be made.
        Setting this set the checkbox to the appropriate value and
        enables/disables the vid_button.
        The checkbox will not emit signals for that change.
        """
        return self.files['vid'] if self.vid_cbox.checkState() else None
    @vid_file.setter
    def vid_file(self, value: str):
        self.vid_cbox.blockSignals(True)
        self.module.vid_file = value
        if value is not None:
            self.vid_cbox.setCheckState(2)
            self.files['vid'] = value
        else:
            self.vid_cbox.setCheckState(0)
        self.vid_button.setEnabled(value is not None)
        self.vid_cbox.blockSignals(False)

    @property
    def in_file(self) -> str:
        """Input file"""
        return self.files['in']
    @in_file.setter
    def in_file(self, value: str):
        self.files['in'] = value
        if self.module is not None:
            self.module.in_file = value

    @property
    def preview(self):
        """Boolean indicating the preview preference

        Setting this set the checkbox to the appropriate value.
        The checkbox will not emit signals for that change.
        No setter is implemented.
        """
        return bool(self.preview_cbox.checkState())

    @property
    def running(self):
        """Boolean indicating the state of the system.

        Setting this to True will cause a progress bar to become visible and the
        button label to change to 'Cancel'. Go will be set if the value is set to False.
        """
        return self._running
    @running.setter
    def running(self, value: bool):
        # pylint: disable=attribute-defined-outside-init
        self._running = value
        for widget in self.disabled_group:
            widget.setEnabled(not self._running)
        if self.module is not None:
            self.module.enabled = not value
            self.module.running = value
        #self.custom.thread.running = value
        # This might seem strange and effectless, but it does reset the buttons
        # to the correct state.
        # Disables csv and video selections buttons
        self.csv_button.setEnabled(not value)
        self.vid_button.setEnabled(not value)
        if value:
            self.go_button.setText('Stop')
        else:
            self.go_button.setText('Go')

    @property
    def module(self):
        """The tracking module"""
        return self._module
    @module.setter
    def module(self, value):
        del self.module
        self._module = value
        self.module_widget = self._module.widget()
        self.custom_box.addWidget(self.module_widget)
    @module.deleter
    def module(self):
        self.custom_box.removeWidget(self.module_widget)
        if self._module is not None:
            self._module.deleteLater()
        if self.module_widget is not None:
            self.module_widget.deleteLater()
        #del self._module

    @property
    def enabled(self) -> bool:
        """Enabledness of the widgets"""
        return self._enabled
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        for widget in self.disabled_group:
            widget.setEnabled(value)
        self.module.enabled = value

    def __init__(self, module=None):
        super().__init__('Options')
        self.setFeatures(QDockWidget.DockWidgetMovable)
        self.files = {'csv': None, 'vid': None}
        self._module = None
        self.module_widget = None
        self.create_gui()
        if module:
            self.module = module
        self.running = False
        self._enabled = True

    def emit_go(self):
        """Emits a go signal"""
        # This boolean value needs to emit the negated running state
        self.started.emit(not self.running)

    def pick_csv(self):
        """Picks csv output location

        Spawns a QFileDialog to get a save file name. Defaults to currently set csv_file.
        If successful will change self.csv_file
        """
        file_name = QFileDialog.getSaveFileName(self, 'CSV File Save Location',
                                                self.csv_file, '*.csv')
        if file_name[0]:
            self.csv_file = file_name[0]

    def pick_vid(self):
        """Picks video output location

        Spawns a QFileDialog to get a save file name. Defaults to currently set vid_file.
        If successful will change self.vid_file
        """
        file_name = QFileDialog.getSaveFileName(self, 'Video save location',
                                                self.vid_file, '*.mp4')
        if file_name[0]:
            self.vid_file = file_name[0]

    def set_vid(self, change: int):
        """Sets the video output to the change value"""
        if bool(change):
            self.vid_file = self.files['vid']
        else:
            self.vid_file = None

    def set_csv(self, change: int):
        """Sets the csv output to the change value"""
        if bool(change):
            self.csv_file = self.files['csv']
        else:
            self.csv_file = None

    def create_gui(self):
        """Creates the dock gui

        The dock gui consists of a vbox with a grid in the lower end, and a
        custom widget in the upper end. They are separated by a stretch.

        The grid has checkboxes for enabling/disabling csv and vid, as well as
        setting vid_file and csv_file.
        """
        # Elements
        self.csv_cbox = QCheckBox('Output CSV', stateChanged=self.set_csv,
                                  statusTip='Enable CSV output')
        self.csv_button = QPushButton('File...', enabled=self.csv_cbox.checkState(),
                                      clicked=self.pick_csv,
                                      maximumWidth=50,
                                      statusTip='Output CSV')
        self.vid_cbox = QCheckBox('Output Video', statusTip='Enable Video output',
                                  stateChanged=self.set_vid)
        self.vid_button = QPushButton('File...', enabled=self.vid_cbox.checkState(),
                                      clicked=self.pick_vid,
                                      maximumWidth=50,
                                      statusTip='Output video')
        self.preview_cbox = QCheckBox('Preview', statusTip='Show video during computation',
                                      checked=True)
        self.go_button = QPushButton('Go', maximumWidth=50, clicked=self.emit_go, enabled=False)
        #self.preview_cbox.stateChanged.connect(lambda x: setattr(self.custom.thread, 'draw', bool(x)))
        # Grid layout
        inner_grid = QGridLayout()
        inner_grid.addWidget(self.csv_cbox, 0, 0)
        inner_grid.addWidget(self.csv_button, 0, 1)
        inner_grid.addWidget(self.vid_cbox, 1, 0)
        inner_grid.addWidget(self.vid_button, 1, 1)
        inner_grid.addWidget(self.preview_cbox, 2, 0)
        inner_grid.addWidget(self.go_button, 2, 1)
        self.disabled_group = [
            self.csv_cbox, self.csv_button,
            self.vid_cbox, self.vid_button,
        ]
        # wrapped in a vbox
        layout = QVBoxLayout()
        self.custom_box = QBoxLayout(1)
        layout.addLayout(self.custom_box)
        layout.addStretch(1)
        layout.addLayout(inner_grid)
        # wrapped in a widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setWidget(widget)
        self.disabled_group = [self.csv_cbox, self.csv_button, self.vid_cbox, self.vid_button]
