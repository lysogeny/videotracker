"""Widgets of the video-tracker"""

from PyQt5.QtWidgets import (QWidget, QMainWindow, QAction, #QMessageBox,
                             QFileDialog, qApp, QCheckBox, QPushButton,
                             QGridLayout, QDockWidget, QVBoxLayout, QBoxLayout,
                             QProgressBar, QLabel, QSizePolicy, QScrollArea,
                             QSlider, QHBoxLayout, QSpinBox)
from PyQt5.QtGui import QIcon, QPalette, QImage, QPixmap
from PyQt5.QtCore import Qt

import cv2

class ImageView(QWidget):
    """The view area.

    The view area consists of a label with a pixmap in a scrollarea
    """
    @property
    def scale(self):
        """The scale of the image"""
        return self._scale
    @scale.setter
    def scale(self, value):
        # pylint: disable=attribute-defined-outside-init
        self._scale = value
        if self.image_lab.pixmap():
            self.image_lab.resize(self.scale * self.image_lab.pixmap().size())

    @property
    def image(self):
        """The image displayed"""
        return self.frame
    @image.setter
    def image(self, frame):
        first = self.frame is None
        self.frame = frame
        height, width, channels = frame.shape
        bytes_per_line = channels*width
        qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.image_lab.setPixmap(QPixmap.fromImage(qimg))
        self.slider.setEnabled(True)
        self.sbox.setEnabled(True)
        if first:
            self.scale = 1.0
        else:
            self.scale = self.scale

    @property
    def pos_max(self):
        """The maximum position possible"""
        return self._pos_max
    @pos_max.setter
    def pos_max(self, value):
        # Attribute actually gets defined in init, pylint is confused by this
        # pylint: disable=attribute-defined-outside-init
        self._pos_max = value
        self.slidelabel.setText(self.lab_text_template.format(self.pos, value))
        self.sbox.setMaximum(value)
        self.slider.setMaximum(value)

    @property
    def pos(self):
        """Position of the slider and video"""
        return self.slider.value()
    @pos.setter
    def pos(self, value):
        self.slider.setValue(value)
        self.sbox.setValue(value)
        self.slidelabel.setText(self.lab_text_template.format(value, self.pos_max))

    def __init__(self):
        super().__init__()
        self.lab_text_template = '{:}/{:}'
        self.create_gui()
        self.pos_max = 0
        self.frame = None

    def create_gui(self):
        """Creates the image view gui"""
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
        """Reset the widget to avoid issues"""
        self.slider.blockSignals(True)
        self.pos_max = 0
        self.pos = 0
        self.slider.blockSignals(False)

    def zoom_in(self):
        """Zooms in"""
        self.scale *= 1.25

    def zoom_out(self):
        """Zooms out"""
        self.scale *= 0.8

    def zoom_optimal(self):
        """Zooms to normal extent"""
        current_width = self.image_lab.width()
        should_width = self.scrollarea.width()
        current_height = self.image_lab.height()
        should_height = self.scrollarea.height()
        self.scale = min(should_width/current_width * self.scale,
                         should_height/current_height * self.scale)

class SideDock(QDockWidget):
    """Sidebar dock area"""
    @property
    def csv_file(self):
        """Output location of the csv file.

        None if self.csv False, otherwise str
        """
        if self.csv:
            return self.files['csv']
        return None
    @csv_file.setter
    def csv_file(self, value: str):
        self.files['csv'] = value
        self.csv_button.setStatusTip(value)

    @property
    def vid_file(self):
        """Output location of the video file.

        None if self.vid False, otherwise str
        """
        if self.vid:
            return self.files['vid']
        return None
    @vid_file.setter
    def vid_file(self, value: str):
        self.files['vid'] = value
        self.vid_button.setStatusTip(value)

    @property
    def csv(self):
        """Boolean indicating csv output"""
        return bool(self.csv_cbox.checkState())
    @csv.setter
    def csv(self, value: bool):
        self.csv_cbox.setCheckState(value)
        self.csv_button.setEnabled(self.csv)

    @property
    def vid(self):
        """Boolean indicating vid output"""
        return bool(self.vid_cbox.checkState())
    @vid.setter
    def vid(self, value: bool):
        self.vid_cbox.setCheckState(value)
        self.vid_button.setEnabled(self.vid)

    @property
    def preview(self):
        """Boolean indicating the preview preference"""
        return bool(self.preview_cbox.checkState())
    @preview.setter
    def preview(self, value: bool):
        if value:
            self.preview_cbox.setCheckState(2)
        else:
            self.preview_cbox.setCheckState(0)

    @property
    def running(self):
        """Boolean indicating the state of the system."""
        return self._running
    @running.setter
    def running(self, value: bool):
        # pylint: disable=attribute-defined-outside-init
        self._running = value
        if self._running:
            self.go_button.setText('Pause')
            self.progress.setVisible(True)
        else:
            self.go_button.setText('Go')
            #self.progress.setVisible(False)

    def __init__(self, custom=None):
        super().__init__('Options')
        self.setFeatures(QDockWidget.DockWidgetMovable)
        self.files = {'csv': None, 'vid': None}
        self.custom = custom
        self.create_gui()
        self.preview = True
        self.running = False

    def pick_csv(self):
        """Picks csv output location"""
        file_name = QFileDialog.getSaveFileName(self, 'CSV File Save Location',
                                                self.csv_file, '*.csv')
        if file_name[0]:
            self.csv_file = file_name[0]

    def pick_vid(self):
        """Picks video output location"""
        file_name = QFileDialog.getSaveFileName(self, 'Video save location',
                                                self.vid_file, '*.mp4')
        if file_name[0]:
            self.vid_file = file_name[0]

    def create_gui(self):
        """Creates the dock gui"""
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
        self.preview_cbox = QCheckBox('Preview', statusTip='Should video during computation',
                                      stateChanged=lambda x: setattr(self, 'checked', bool(x)))
        self.progress = QProgressBar()
        self.progress.setHidden(True)
        self.go_button = QPushButton('Go', maximumWidth=50,
                                     clicked=lambda x:setattr(self, 'running', not self.running),
                                     enabled=False)
        # Grid layout
        inner_grid = QGridLayout()
        inner_grid.addWidget(self.csv_cbox, 0, 0)
        inner_grid.addWidget(self.csv_button, 0, 1)
        inner_grid.addWidget(self.vid_cbox, 1, 0)
        inner_grid.addWidget(self.vid_button, 1, 1)
        inner_grid.addWidget(self.preview_cbox, 2, 0)
        inner_grid.addWidget(self.go_button, 2, 1)
        inner_grid.addWidget(self.progress, 3, 0, 3, 3)
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


class ThresholdSegmentWidget(QWidget):
    """A threshold segmentation widget"""

class MainView(QMainWindow):
    """An abstract main view"""

    TITLE = 'pyqt-stuff'
    actions = {}
    menus_in_bar = ['&File', '&View']

    def __init__(self):
        super().__init__()
        self.create_gui()
        self.create_actions()
        self.setWindowTitle(self.TITLE)
        self.video_file = None
        self.frame = None
        self.capture = None

    def create_gui(self):
        """Creates the GUI"""
        # Bars
        self.toolbar = self.addToolBar('View')
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Ready')
        # Dock
        self.dock = SideDock(QPushButton())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        # Image
        self.image = ImageView()
        self.image.slider.valueChanged.connect(self.grab_frame)
        self.setCentralWidget(self.image)
        self.resize(800, 500)

    def create_actions(self):
        """Creates all actions"""
        # pylint: disable=no-self-use
        # No clue why pylint thinks that this could be a function while it is
        # clearly an abstracted method.
        self.actions = {
            '&File': [
                QAction(QIcon.fromTheme('document-open'), 'Open...',
                        statusTip='Opens a new file',
                        triggered=self.video_load)
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
                QAction(QIcon.fromTheme('media-playback-start'), 'Play',
                        statusTip='Plays the video',
                        shortcut='Space', checkable=True, enabled=False),
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
                # Only add actions where I added an icon
                if menu in self.menus_in_bar and not action.icon().isNull():
                    self.toolbar.addAction(action)

    def grab_frame(self, number: int):
        """Grabs frame number from the video device"""
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, number)
        _, self.frame = self.capture.read()
        self.image.image = self.frame

    def video_load(self):
        """Loads a video file"""
        file_name = QFileDialog.getOpenFileName(self, 'Open file', self.video_file)
        if file_name[0]:
            # Open the video, get first frame
            self.video_file = file_name[0]
            self.capture = cv2.VideoCapture(self.video_file)
            _, self.frame = self.capture.read()
            # Set image of imageviewer, new maximum position
            self.image.reset()
            self.image.image = self.frame
            self.image.pos_max = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))-1
            print('got')
            # Enable all view actions
            for action in self.actions['&View']:
                action.setEnabled(True)
            # Print message
            self.statusbar.showMessage('Loaded file {}'.format(self.video_file))
            # Enable dock go button
            self.dock.go_button.setEnabled(True)
            # Give dock some basic idea of file names
            file_name_base = '.'.join(file_name[0].split('.')[:-1])
            if not self.dock.vid_file:
                self.dock.vid_file = file_name_base + '_output.' + 'mp4'
            if not self.dock.csv_file:
                self.dock.csv_file = file_name_base + '_output.' + 'csv'
