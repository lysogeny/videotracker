"""Windows of the videotracker

This module contains all of the windows that the videotracker uses.
"""

from PyQt5 import QtWidgets

from . import widgets
from . import segmentations
from . import helpers

class MainWindow(QtWidgets.QMainWindow):
    """The Main Window of the videotracker.

    This is the window that is spawned when the application is called.
    """

    TITLE = 'pyqt-videotracker'

    # The properties of this window
    @property
    def loaded(self) -> bool:
        """Boolean indicating if a video file has been loaded"""
        return self.state['loaded']
    @loaded.setter
    def loaded(self, value: bool):
        self.state['loaded'] = value
        for widget in self.widgets:
            self.widgets[widget].loaded = value

    @property
    def running(self) -> bool:
        """Boolean indicating if a thread is running a segmentation

        This is used to determine who has control over the frame loaded.
        """
        return self.state['running']
    @running.setter
    def running(self, value: bool):
        self.state['running'] = value
        for widget in self.widgets:
            self.widgets[widget].running = value

    @property
    def module(self):
        """The module that does things"""
    @module.setter
    def module(self, value):
        pass

    @property
    def csv(self) -> str:
        """The csv file to output things"""
        return self.files['csv']
    @csv.setter
    def csv(self, value: str):
        self.files['csv'] = value

    @property
    def vid(self) -> str:
        """The video file to output things"""
        return self.files['vid']
    @vid.setter
    def vid(self, value: str):
        self.files['vid'] = value

    @property
    def input(self) -> str:
        """The input file to input things"""
        return self.files['input']
    @input.setter
    def input(self, value: str):
        self.files['input'] = value

    def __init__(self, *args, module=segmentations.Stack, **kwargs):
        super().__init__(*args, **kwargs)
        # State and files
        self.state = {'loaded': False, 'running': False}
        self.files = {'csv': None, 'vid': None, 'input': None}
        # Create the GUI
        self.create_gui()
        self.create_actions()
        self.module = module

    def create_gui(self):
        """Creates the GUI of the application"""
        self.widgets = {
            'image': widgets.ImageView(),
            'sidebar': None,
            'menubar': self.menuBar(),
            'toolbar': self.addToolBar('Main'),
            'statusbar': self.statusBar(),
        }
        self.widgets['statusbar'].showMessage('Ready')
        self.setWindowTitle(self.TITLE)

    def create_actions(self):
        """Creates all relevant actions of the application"""
        self.actions = {
            'help': 'No'
        }
        for menu in self.actions:
            # Add a menu with that name
            this_menu = self.widgets['menubar'].addMenu(menu)
            for action in self.actions[menu]:
                # Add the action to the menu
                this_menu.addAction(self.actions[menu][action])
                # Only add actions to the toolbar that have icons and are not
                # help actions
                if menu not in ('&Help') and not action.icon().isNull():
                    self.widgets['toolbar'].addAction(action)

    def pick_module(self, module):
        """Loads a sidebar module

        Spawns a module picker that allows the user to change out the module on the fly.
        """
        self.module = module

    def load_video(self, video_file):
        """Load a video file"""
        if video_file:
            self.vid = self.video_file
