"""Windows of the videotracker"""

import os
import inspect
#import importlib

from PyQt5 import QtWidgets, QtCore, QtGui

#import cv2

from . import helpers, segmentations, widgets


class ModuleDialog(QtWidgets.QDialog):
    """A dialog for choosing a module"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setModal(True)
        self.create_gui()
        self.populate_list()
        self._result = self.exec_() == self.Accepted

    def create_gui(self):
        """Creates the gui of the dialog"""
        self.widget = QtWidgets.QListWidget()
        self.widget.doubleClicked.connect(self.accept)
        okay = QtWidgets.QPushButton('OK', clicked=self.accept)
        cancel = QtWidgets.QPushButton('Cancel', clicked=self.reject)
        more = QtWidgets.QPushButton('Load...', clicked=self.load_file,
                                     toolTip='Source another python module',
                                     enabled=False)
        sub_layout = QtWidgets.QHBoxLayout()
        sub_layout.addWidget(more)
        sub_layout.addStretch(1)
        sub_layout.addWidget(cancel)
        sub_layout.addWidget(okay)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addLayout(sub_layout)
        self.setLayout(layout)
        self.setWindowTitle('Module Choices')
        self.options = {}

    def load_file(self):
        """Loads another file"""
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Load module', None, '*.py')
        return file_name

    def populate_list(self, module=segmentations):
        """Populates the list with options"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) # The item is a class
                    and issubclass(obj, QtWidgets.QWidget) # The class inherits from QWidget
                    and not name.startswith('Base')): # And isn't Abstract
                self.options[name] = obj
                short_name = name
                full_description = obj.__doc__
                #short_description = full_description.split('\n')[0]
                item = QtWidgets.QListWidgetItem(short_name)
                item.setToolTip(full_description)
                self.widget.addItem(item)

    @property
    def value(self):
        """Returns value of the module dialog"""
        name = self.widget.currentItem().text()
        return self.options[name]

    @property
    def result(self):
        """Returns a result, True or False, indicating if okay or cancel was chosen"""
        return self._result

class MainView(QtWidgets.QMainWindow, widgets.BaseFileObject):
    """A main view

    This main view has four principal states consisting of a combination of
    running and loaded.
    These states define which GUI elements are enabled at which given timepoint.

    This widget unites a ImageView and SideDock widget
    """
    # Is 8/7 instance attributes really too many? Considering that this is a
    # main window, that is impressively low.
    # pylint: disable=too-many-instance-attributes

    TITLE = 'pyqt-videotracker'
    actions = {}
    def __init__(self, csv_file=None, vid_file=None, in_file=None, config=None, debug=True):
        super().__init__()
        self.state = {
            'running': False,
            'loaded': False,
            'image_control': False
        }
        self.debug = debug
        self.create_gui()
        self.create_actions()
        self.setWindowTitle(self.TITLE)
        self.options = None
        self.module_load()
        # Todo: load module config
        self.in_file = in_file
        self.csv_file = csv_file
        self.vid_file = vid_file
        if self.in_file is not None:
            self.input_load()
        print(self.files)

    @property
    def has_module(self) -> bool:
        """Boolean indicating if a module is loaded."""
        return self.options is not None

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
            start_action.setIcon(QtGui.QIcon.fromTheme('media-playback-stop'))
            start_action.setText('Stop')
        else:
            start_action.setIcon(QtGui.QIcon.fromTheme('media-playback-start'))
            start_action.setText('Start')
        # Disable option controls
        for widget in self.widgets:
            self.widgets[widget].enabled = not value
        self.image_control = not value
        self.dock.running = value

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
        helpers.disconnect(self.options.pos_changed)
        helpers.disconnect(self.image.pos_changed)
        if value:
            conn = self.image.pos_changed.connect(self.options.video.fetch, type=QtCore.Qt.QueuedConnection)
        else:
            self.options.pos_changed.connect(self.image.set_pos)
        self.image.enabled = value

    @property
    def in_file(self) -> str:
        """A file handle describing the input (str)"""
        return self.files['in'] if self.loaded else None
    @in_file.setter
    def in_file(self, value: str):
        self.files['in'] = value
        for widget in self.widgets:
            try:
                self.widgets[widget].in_file = value
            except AttributeError:
                pass
        if value is None:
            self.loaded = False
        else:
            self.loaded = True

    @property
    def vid_file(self) -> str:
        return self.dock.vid_file
    @vid_file.setter
    def vid_file(self, value: str):
        self.dock.vid_file = value
        self.files['vid'] = value

    @property
    def csv_file(self) -> str:
        return self.dock.csv_file
    @csv_file.setter
    def csv_file(self, value: str):
        self.dock.csv_file = value
        self.files['csv'] = value

    def create_gui(self):
        """Creates the GUI"""
        # Bars
        self.toolbar = self.addToolBar('View')
        self.menubar = self.menuBar()
        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Ready')
        # Dock
        self.dock = widgets.SideDock()
        self.dock.started.connect(lambda x: setattr(self, 'running', x))
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)
        # Image
        self.image = widgets.ImageView()
        self.setCentralWidget(self.image)
        self.resize(800, 500)
        self.widgets = {
            'image': self.image,
            'dock': self.dock,
        }

    def create_actions(self):
        """Creates all actions and places them into menus and bars"""
        self.actions = {
            '&File': [
                QtWidgets.QAction(QtGui.QIcon.fromTheme('document-open'), 'Open...',
                                  statusTip='Opens a new file',
                                  triggered=self.input_pick),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('window-new'), 'Module...',
                                  statusTip='Loads a tracking module',
                                  triggered=self.module_pick),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('process-stop'), 'Break...',
                                  statusTip='Inserts a breakpoint', shortcut='Del',
                                  triggered=self.breakpoint,
                                  enabled=self.debug),
            ],
            '&View': [
                QtWidgets.QAction(QtGui.QIcon.fromTheme('zoom-in'), 'Zoom in',
                                  statusTip='Increases scale',
                                  triggered=self.image.zoom_in,
                                  shortcut='PgDown',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('zoom-out'), 'Zoom out',
                                  statusTip='Decreases scale',
                                  triggered=self.image.zoom_out,
                                  shortcut='PgUp',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('zoom-original'), 'Zoom normal',
                                  statusTip='Sets scale to 1.0',
                                  triggered=lambda: setattr(self.image, 'scale', 1.0),
                                  shortcut='Ctrl+1',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('zoom-fit-best'), 'Zoom optimal',
                                  statusTip='Sets scale to 1.0',
                                  triggered=self.image.zoom_optimal,
                                  shortcut='Ctrl+2',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('media-playback-start'),
                                  'Start segmentation',
                                  statusTip='Segmentation is started',
                                  shortcut='Space', enabled=False,
                                  triggered=lambda: setattr(self, 'running', not self.running)),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('go-first'), 'Goto first frame',
                                  statusTip='Goes to the first frame',
                                  triggered=lambda: setattr(self.image, 'pos', 0),
                                  shortcut='[',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('go-previous'), 'Goto previous frame',
                                  statusTip='Goes to the previous frame',
                                  triggered=lambda: setattr(self.image, 'pos', self.image.pos-1),
                                  shortcut=',',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('go-next'), 'Goto next frame',
                                  statusTip='Goes to the next frame',
                                  triggered=lambda: setattr(self.image, 'pos', self.image.pos+1),
                                  shortcut='.',
                                  enabled=False),
                QtWidgets.QAction(QtGui.QIcon.fromTheme('go-last'), 'Goto last frame',
                                  statusTip='Goes to the last frame',
                                  triggered=lambda: setattr(self.image, 'pos', self.image.pos_max),
                                  shortcut=']',
                                  enabled=False),
                QtWidgets.QAction('Show toolbar',
                                  checkable=True,
                                  checked=True,
                                  statusTip='Visibility of the toolbar',
                                  triggered=self.toolbar.setVisible)
            ],
            '&Help': [
                QtWidgets.QAction(QtGui.QIcon.fromTheme('help-about'), 'About Qt',
                                  statusTip='Help, I am stuck in a GUI factory',
                                  triggered=QtWidgets.qApp.aboutQt),
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

    def breakpoint(self):
        """This is a breakpoint"""
        import ipdb; ipdb.set_trace()  # XXX BREAKPOINT

    def input_pick(self):
        """Spawn a video picking dialog"""
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.vid_file)
        if file_name[0]:
            self.input_load(file_name[0])

    def input_load(self, video_file=None):
        """Loads a video file"""
        self.image.pos = 0 # ImageViewer gets a new position
        if video_file is None:
            test_file = self.in_file
        else:
            test_file = video_file
        if test_file is not None:
            self.image.pos_max = helpers.video_max_frame(test_file)
        # ImageViewer gets a new max_position
        # Input is defined, CSV and video output files are guessed.
        # All of these propagate into the subwidgets.
        if video_file is not None:
            self.in_file = video_file
        file_tokenised = os.path.splitext(self.in_file)
        self.csv_file = f'{file_tokenised[0]}_output.csv'
        self.vid_file = f'{file_tokenised[0]}_output{file_tokenised[1]}'
        self.setWindowTitle(f'{self.TITLE} {self.in_file}')
        self.statusbar.showMessage(f'Loaded file {self.in_file}')

    def module_pick(self):
        """Spawns a picker dialog for modules"""
        dialog = ModuleDialog()
        if dialog.result:
            module = dialog.value
            print('User chose new module {}'.format(module))
            self.module_load(module)

    def module_load(self, method=segmentations.ShortStack):
        """Creates a dock with the given method"""
        # Delete old options
        # Create new options
        self.options = method() # Method is constructed
        self.dock.module = self.options
        self.options.view_changed.connect(lambda: setattr(self.image, 'image', self.options.view.data))
        self.options.output_changed.connect(lambda: setattr(self.image, 'image', self.options.view.data))
        #self.image.source = self.options.view
        #self.options.thread.finished.connect(lambda: setattr(self, 'running', False))
        #self.options.thread.loop_complete.connect(lambda: setattr(self, 'running', False))
        #self.options.thread.computing.connect(helpers.change_cursor)
