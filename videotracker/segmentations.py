"""Various segmentation methods"""
import cv2

def segmentation(args):
    class Segment(Segmentation):
        def __init__(self, fun):
            self.fun = fun
        def __call__(self, *args, **kwargs):
            fun(*args, **kwargs)
    Segment(

@segment
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

class ThresholdSegmentation:
    """Threshold Segmentation"""
