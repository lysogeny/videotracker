"""Various segmentation methods"""
import cv2

class ThresholdSegmentationWidget(QWidget):
    """A threshold segmentation widget"""

    def __init__(self):
        super().__init__()
        self.widgets = {}
        self.create_gui()
        self.create_methods()

    @property
    def c(self):
        # c is snek_case.
        # pylint: disable=invalid-name
        """Value subtracted from all bins"""
        return self.widgets['C Value'].value()
    @c.setter
    def c(self, value):
        # c is snek_case.
        # pylint: disable=invalid-name
        self.widgets['C Value'].setValue(value)

    def create_gui(self):
        """Creates a GUI"""
        self.parameters = [
            {'name': 'blur',
             'label': 'Blur Size',
             'form': QSpinBox,
             'range': (1, 100),
             'validity': lambda x: not x % 2},
            {'name': 'c',
             'label': 'C Value',
             'form': QSpinBox},
            {'name': 'size',
             'label': 'Bin Size',
             'form': QSpinBox,
             'validity': lambda x: not x % 2},
            {'name': 'minimum',
             'label': 'Minimum Size',
             'form': QSpinBox},
            {'name': 'maximum',
             'label': 'Maximum Size',
             'form': QSpinBox},
            {'label': 'Gaussian',
             'form': QCheckBox},
        ]
        layout = QGridLayout()
        self.setLayout(layout)
        for i, parameter in enumerate(self.parameters):
            widget = parameter['form']()
            self.widgets[parameter['name']] = widget
            label = QLabel(parameter['label'])
            # add bits to layout
            layout.addWidget(widget, i, 0)
            layout.addWidget(label, i, 1)

    #def create_methods(self):
    #    """Creates class properties and methods based on parameters given"""
    #    for i, parameter in enumerate(self.parameters):
    #        name = copy.copy(parameter['name'])
    #        if 'validity' in parameter.keys():
    #            validity = copy.copy(parameter['validity'])
    #        else:
    #            validity = lambda x: True
    #        def getter(self):
    #            return self.widgets[name].value()
    #        def setter(self, value):
    #            if parameter['validity'](value):
    #                self.widgets[name].setValue(value)


def adaptive_gaussian_threshold(img, size=11, value=3):
    """Adaptive threshold
    Params
    ------
    size: Size
    value: Value

    Applies adaptive threshold of size size and with C value to img"""
    return cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY_INV, size, value)

class Segmentation:
    """Base segmentation"""
    function_stack = [
    ]

    def __init__(self):
        self.params = [fun.params for fun in self.function_stack]

    def __call__(self, frame):
        img = frame.copy()
        for function in self.function_stack:
            img = function(img)

def segmentation(args):
    class Segment(Segmentation):
        """A Segmentation"""
        def __init__(self, fun):
            self.fun = fun
        def __call__(self, *args, **kwargs):
            self.fun(*args, **kwargs)


class ThresholdSegmentation:
    """Threshold Segmentation"""
