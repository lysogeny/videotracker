"""Widgets of the video-tracker"""

#import copy
#from collections import defaultdict
import os

from PyQt5.QtWidgets import (QWidget, QMainWindow, QAction, #QMessageBox,
                             QFileDialog, qApp, QCheckBox, QPushButton,
                             QGridLayout, QDockWidget, QVBoxLayout, QBoxLayout,
                             QLabel, QSizePolicy, QScrollArea, QSlider,
                             QHBoxLayout, QSpinBox, QColorDialog)
from PyQt5.QtGui import QIcon, QPalette, QImage, QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal

import cv2

from . import segmentations
from . import helpers
from .video import Video

class ColourButton(QPushButton):
    """A button, that when pushed, returns a colour"""

    valueChanged = pyqtSignal(str)

    def value(self):
        """The value of the widget"""
        return self._color.name()

    def pick_colour(self):
        """Pick the colour using the dialog"""
        self._color = self.dialog.getColor(self._color)
        self.setValue(self._color.name())

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

    pos_changed = pyqtSignal(int)
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
            - An image to be converted to a QImage and then displayed in the
              ScrollArea
            - Spinboxes, Sliders to be enabled
            - If this is the first image to be loaded, scale set to 1.0

        The numpy array is stored in self.frame
        """
        return self.frame
    @image.setter
    def image(self, frame):
        first = self.frame is None
        self.frame = frame
        height, width, channels = frame.shape
        bytes_per_line = channels*width
        qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_lab.setPixmap(QPixmap.fromImage(qimg))
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

    def set_position(self, value: int):
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

    def __init__(self):
        super().__init__()
        self.lab_text_template = '{:}/{:}'
        self.create_gui()
        self.pos_max = 0
        self.frame = None
        self._enabled = False

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
        self.image_lab.setBackgroundRole(QPalette.Dark)
        self.image_lab.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_lab.setScaledContents(True)
        self.scrollarea = QScrollArea()
        self.scrollarea.setBackgroundRole(QPalette.Dark)
        self.scrollarea.setWidget(self.image_lab)
        self.slidelabel = QLabel(self.lab_text_template.format(0, 0))
        self.slider = QSlider(Qt.Horizontal, enabled=False,
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

class SideDock(QDockWidget):
    """Sidebar dock area

    Consists of an upper custom widget (defined by custom in construction) and a
    lower constant widget. The lower widget adjust various output file
    properties, and offers controls for starting/stopping.
    """
    # Again, pylint disagrees on instance attributes.
    # To my count there is seven-ish properly public attributes.
    # A further seven attributes define various UI elements which need to be
    # accessed frequently by property setters and getters.
    # As such I don't think there is much room for improvement
    # Arguably, custom could be it's own module, with the layouting done here
    # done in the main window.
    # Perhaps I will change to that, but right now that appears to be a minor
    # issue.
    # pylint: disable=too-many-instance-attributes

    started = pyqtSignal(bool)

    @property
    def csv_file(self):
        """Output location of the csv file.

        None if self.csv False, otherwise str.
        Setting this changes the status tip of the csv_button
        """
        if self.csv:
            return self.files['csv']
        return None
    @csv_file.setter
    def csv_file(self, value: str):
        self.files['csv'] = value
        self.csv_button.setStatusTip(value)
        if self.csv:
            self.custom.thread.csv_file = value
        else:
            self.custom.thread.csv_file = None

    @property
    def vid_file(self):
        """Output location of the video file.

        None if self.vid False, otherwise str.
        Setting this changes the status tip of the vid_button
        """
        if self.vid:
            return self.files['vid']
        return None
    @vid_file.setter
    def vid_file(self, value: str):
        self.files['vid'] = value
        self.vid_button.setStatusTip(value)
        if self.vid:
            self.custom.thread.vid_file = value
        else:
            self.custom.thread.vid_file = None

    @property
    def csv(self):
        """Boolean indicating csv output

        Setting this set the checkbox to the appropriate value and
        enables/disables the csv_button.
        The checkbox will not emit signals for that change.
        """
        return bool(self.csv_cbox.checkState())
    @csv.setter
    def csv(self, value: bool):
        self.csv_cbox.blockSignals(True)
        if value:
            self.csv_cbox.setCheckState(2)
            self.custom.thread.csv_file = self.csv_file
        else:
            self.csv_cbox.setCheckState(0)
            self.custom.thread.csv_file = None
        self.csv_cbox.blockSignals(False)
        self.csv_button.setEnabled(self.csv)

    @property
    def vid(self):
        """Boolean indicating vid output

        Setting this set the checkbox to the appropriate value and
        enables/disables the vid_button.
        The checkbox will not emit signals for that change.
        """
        return bool(self.vid_cbox.checkState())
    @vid.setter
    def vid(self, value: bool):
        self.vid_cbox.blockSignals(True)
        if value:
            self.vid_cbox.setCheckState(2)
            self.custom.thread.vid_file = self.vid_file
        else:
            self.vid_cbox.setCheckState(0)
            self.custom.thread.vid_file = None
        self.vid_cbox.blockSignals(False)
        self.vid_button.setEnabled(self.vid)

    @property
    def preview(self):
        """Boolean indicating the preview preference

        Setting this set the checkbox to the appropriate value.
        The checkbox will not emit signals for that change.
        """
        return bool(self.preview_cbox.checkState())
    @preview.setter
    def preview(self, value: bool):
        self.preview_cbox.blockSignals(True)
        if value:
            self.preview_cbox.setCheckState(2)
        else:
            self.preview_cbox.setCheckState(0)
        self.preview_cbox.blockSignals(False)

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
        self.custom.enabled = not value
        self.custom.thread.running = value
        # This might seem strange and effectless, but it does reset the buttons
        # to the correct state.
        self.vid = self.vid
        self.csv = self.csv
        # Disables csv and video selections buttons
        self.csv_button.setEnabled(not value)
        self.vid_button.setEnabled(not value)
        if value:
            self.go_button.setText('Stop')
        else:
            self.go_button.setText('Go')

    def __init__(self, custom=None):
        super().__init__('Options')
        self.setFeatures(QDockWidget.DockWidgetMovable)
        self.files = {'csv': None, 'vid': None}
        self.custom = custom
        self.create_gui()
        self.preview = True
        self.running = False

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

    def create_gui(self):
        """Creates the dock gui

        The dock gui consists of a vbox with a grid in the lower end, and a
        custom widget in the upper end. They are separated by a stretch.

        The grid has checkboxes for enabling/disabling csv and vid, as well as
        setting vid_file and csv_file.
        """
        # Elements
        self.csv_cbox = QCheckBox('Output CSV', stateChanged=lambda x: setattr(self, 'csv', x),
                                  statusTip='Enable CSV output')
        self.csv_button = QPushButton('File..', enabled=self.csv_cbox.checkState(),
                                      clicked=self.pick_csv,
                                      maximumWidth=50,
                                      statusTip='Output CSV')
        self.vid_cbox = QCheckBox('Output Video', statusTip='Enable Video output',
                                  stateChanged=lambda x: setattr(self, 'vid', x))
        self.vid_button = QPushButton('File..', enabled=self.vid_cbox.checkState(),
                                      clicked=self.pick_vid,
                                      maximumWidth=50,
                                      statusTip='Output video')
        self.preview_cbox = QCheckBox('Preview', statusTip='Show video during computation',
                                      stateChanged=lambda x: setattr(self, 'checked', bool(x)))
        self.go_button = QPushButton('Go', maximumWidth=50, clicked=self.emit_go, enabled=False)
        self.preview_cbox.stateChanged.connect(lambda x: setattr(self.custom.thread, 'draw', bool(x)))
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
        self.custom_box.addWidget(self.custom)
        layout.addLayout(self.custom_box)
        layout.addStretch(1)
        layout.addLayout(inner_grid)
        # wrapped in a widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setWidget(widget)

class MainView(QMainWindow):
    """A main view

    This main view has four principal states consisting of a combination of
    running and loaded.
    These states define which GUI elements are enabled at which given timepoint.

    This widget unites a ImageView and SideDock widget
    """
    # Is 8/7 instance attributes really too many? Considering that this is a
    # main window, that is impressively low.
    # pylint: disable=too-many-instance-attributes

    TITLE = 'pyqt-stuff'
    actions = {}

    @property
    def running(self) -> bool:
        """Running state of the main window"""
        return self.state['running']
    @running.setter
    def running(self, value: bool):
        # set internal variable
        self.state['running'] = value
        # Disable framecontrol actions
        for action in self.actions['&View'][5:9]:
            action.setEnabled(not value)
        self.actions['&File'][0].setEnabled(not value)
        start_action = self.actions['&View'][4]
        if value:
            start_action.setIcon(QIcon.fromTheme('media-playback-stop'))
            start_action.setText('Stop')
        else:
            start_action.setIcon(QIcon.fromTheme('media-playback-start'))
            start_action.setText('Start')
        # Disable option controls
        self.dock.running = value
        # Set mode of subsidiary elements
        # Set the frame control to be handled by the sidebar, allowing it to
        # step to the next frames.
        self.image_control = not value
        self.options.thread.running = value

    @property
    def loaded(self) -> bool:
        """Has a video been loaded?"""
        return self.state['loaded']
    @loaded.setter
    def loaded(self, value: bool):
        self.state['loaded'] = value
        for action in self.actions['&View']:
            action.setEnabled(value)
        self.dock.go_button.setEnabled(value)
        if value:
            self.options.values_changed.connect(self.options.thread.set_options)
            self.options.thread.start()
        else:
            helpers.disconnect(self.options.values_changed)
            self.options.thread.stop()

    @property
    def image_control(self) -> bool:
        """Is the ImageView controlling the frames?

        True: frames controlled by imageview (self.image)
        False: frames controlled by self.options.thread
        """
        return self.state['image_control']
    @image_control.setter
    def image_control(self, value: bool):
        self.state['image_control'] = value
        # Reconnect signals
        helpers.disconnect(self.options.thread.frame_changed)
        helpers.disconnect(self.image.pos_changed)
        if value:
            self.image.pos_changed.connect(self.compute_image)
        else:
            self.options.thread.frame_changed.connect(self.image.set_position)
        self.image.enabled = value

    def __init__(self, csv=None, vid=None, in_vid=None):
        super().__init__()
        self.state = {
            'running': False,
            'loaded': False,
            'image_control': False
        }
        self.create_gui()
        self.create_actions()
        self.setWindowTitle(self.TITLE)
        self.capture = None
        self.running = False
        self.loaded = False
        # Actions based on arguments
        self.video_file = in_vid
        if self.video_file:
            self.video_load()
        self.dock.csv = csv is not None
        self.dock.vid = vid is not None

    def change_cursor(self, value: bool):
        """Changes cursor for the app. When true changes to hourglass, when false to normal"""
        if value:
            qApp.setOverrideCursor(Qt.WaitCursor)
        else:
            qApp.restoreOverrideCursor()

    def create_gui(self):
        """Creates the GUI"""
        # Bars
        self.toolbar = self.addToolBar('View')
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Ready')
        # Dock
        self.options = segmentations.ThresholdSegmentation()
        self.options.results_changed.connect(self.draw_contours)
        #self.options.thread.finished.connect(lambda: setattr(self, 'running', False))
        self.options.thread.loop_complete.connect(lambda: setattr(self, 'running', False))
        self.options.thread.computing.connect(self.change_cursor)
        self.dock = SideDock(self.options)
        self.dock.preview_cbox.stateChanged.connect(self.recompute_image)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.dock.started.connect(lambda x: setattr(self, 'running', x))
        # Image
        self.image = ImageView()
        self.setCentralWidget(self.image)
        self.resize(800, 500)

    def draw_contours(self):
        """Draw contours onto the image device"""
        if self.dock.preview:
            self.image.image = self.options.thread.result

    def recompute_image(self):
        """Recomputes the image"""
        if self.dock.preview and not self.running:
            self.compute_image(index=self.options.thread.position)

    def compute_image(self, index=None):
        """Computes the image using the function from self.options"""
        self.options.thread.set_position(index)

    def create_actions(self):
        """Creates all actions"""
        # pylint: disable=no-self-use
        # No clue why pylint thinks that this could be a function while it is
        # clearly an abstracted method.
        self.actions = {
            '&File': [
                QAction(QIcon.fromTheme('document-open'), 'Open...',
                        statusTip='Opens a new file',
                        triggered=self.video_pick)
            ],
            '&View': [
                QAction(QIcon.fromTheme('zoom-in'), 'Zoom in',
                        statusTip='Increases scale',
                        triggered=self.image.zoom_in,
                        shortcut='PgDown',
                        enabled=False),
                QAction(QIcon.fromTheme('zoom-out'), 'Zoom out',
                        statusTip='Decreases scale',
                        triggered=self.image.zoom_out,
                        shortcut='PgUp',
                        enabled=False),
                QAction(QIcon.fromTheme('zoom-original'), 'Zoom normal',
                        statusTip='Sets scale to 1.0',
                        triggered=lambda: setattr(self.image, 'scale', 1.0),
                        shortcut='Ctrl+1',
                        enabled=False),
                QAction(QIcon.fromTheme('zoom-fit-best'), 'Zoom optimal',
                        statusTip='Sets scale to 1.0',
                        triggered=self.image.zoom_optimal,
                        shortcut='Ctrl+2',
                        enabled=False),
                QAction(QIcon.fromTheme('media-playback-start'), 'Start segmentation',
                        statusTip='Segmentation is started',
                        shortcut='Space', enabled=False,
                        triggered=lambda: setattr(self, 'running', not self.running)),
                QAction(QIcon.fromTheme('go-first'), 'Goto first frame',
                        statusTip='Goes to the first frame',
                        triggered=lambda: setattr(self.image, 'pos', 0),
                        shortcut='[',
                        enabled=False),
                QAction(QIcon.fromTheme('go-previous'), 'Goto previous frame',
                        statusTip='Goes to the previous frame',
                        triggered=lambda: setattr(self.image, 'pos', self.image.pos-1),
                        shortcut=',',
                        enabled=False),
                QAction(QIcon.fromTheme('go-next'), 'Goto next frame',
                        statusTip='Goes to the next frame',
                        triggered=lambda: setattr(self.image, 'pos', self.image.pos+1),
                        shortcut='.',
                        enabled=False),
                QAction(QIcon.fromTheme('go-last'), 'Goto last frame',
                        statusTip='Goes to the last frame',
                        triggered=lambda: setattr(self.image, 'pos', self.image.pos_max),
                        shortcut=']',
                        enabled=False),
                QAction('Show toolbar',
                        checkable=True,
                        checked=True,
                        statusTip='Visibility of the toolbar',
                        triggered=self.toolbar.setVisible)
            ],
            '&Help': [
                QAction(QIcon.fromTheme('help-about'), 'About Qt',
                        statusTip='Help, I am stuck in a GUI factory',
                        triggered=qApp.aboutQt)
            ]
        }
        for menu in self.actions:
            this_menu = self.menubar.addMenu(menu)
            for action in self.actions[menu]:
                this_menu.addAction(action)
                # Only add actions where I added an icon and which aren't in
                # the help menu.
                if menu not in ('&Help') and not action.icon().isNull():
                    self.toolbar.addAction(action)

    def video_pick(self):
        """Spawn a video picking dialog"""
        file_name = QFileDialog.getOpenFileName(self, 'Open file', self.video_file)
        if file_name[0]:
            self.video_file = file_name[0]
            self.video_load()

    def video_load(self, video_file=None):
        """Loads a video file"""
        if video_file:
            self.video_file = video_file
        # we temporarily create a video object to determine the max frames count.
        video_tmp = Video(self.video_file)
        # Get the maximum amount of frames in this video. Because OpenCV is a
        # bit idiotic, we have to do this slightly strangely.  The property you
        # use to get the maximum frames in opencv is a bit buggy and only works
        # sometimes. Other options include iterating over everything, but that
        # is quite slow as well.  Thus here we set the position to the end of
        # the file and then read out the position in frames that we are at.
        # We then have to subtract one, I have no idea why though, but otherwise it crashes.
        self.loaded = False
        self.image.reset()
        video_tmp.capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 1.0)
        self.image.pos_max = int(video_tmp.capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
        video_tmp.close()
        del video_tmp
        self.options.thread.input_file = self.video_file
        self.options.thread.options = self.options.values
        # Set image of imageviewer, new maximum position
        file_tokenised = os.path.splitext(self.video_file)
        self.dock.csv_file = file_tokenised[0] + '_output' + '.csv'
        self.dock.vid_file = file_tokenised[0] + '_output' + file_tokenised[1]
        self.loaded = True
        self.setWindowTitle(self.TITLE + ' ' + self.video_file)
        self.statusbar.showMessage('Loaded file {}'.format(self.video_file))
