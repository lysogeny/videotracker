"""Tools for contours"""

import logging

import cv2

FEATURES = [
    'timestamp',
    'frame',
    #'id',
    'x',
    'y',
    'area',
    'orientation',
    'mean_value',
]

def contour_centroid(contour):
    """Computes centroid of a contour"""
    moments = cv2.moments(contour)
    try:
        centre = (
            int(moments['m10']/moments['m00']),
            int(moments['m01']/moments['m00'])
        )
    except ZeroDivisionError:
        centre = (
            None,
            None
        )
    return centre

def complex_position(contour):
    """Returns the position of a contour's centroid as a complex number."""
    # Complex numbers are a particularily handy way of encoding position in a 2D
    # plane, as a lot of notational redundancy gets shortened quite a bit.
    # Consider using this.
    if contour is not None:
        return complex(*contour_centroid(contour))

def contour_orientation(contour):
    """Computes a contour's orientation.

    Keep in mind that the orientation has no front-back differentation and your
    result might be flipped 180°. The more points you have, the more accurate
    this will be, and the longer your object is, the more accurate it will be.
    Below a certain threshold (I think 5 points) it will fail and return None
    """
    # Ellipse orientation is last index of the fitEllipse function
    # Alternative orientation metrics are bound to exist, this is something that
    # is fairly simple. It only works with contours >8 points however
    try:
        return cv2.fitEllipse(contour)[-1]
    except cv2.error as error:
        logging.error(error)
        return None

# This dictionary defines function that calculate certain metrics from contours.
# It is used by the extract_features function to find suitable callables that
# produce outputs.
# Functions here need to accept contours as their first argument.
FEATURES = {
    'area': cv2.contourArea,
    'orientation': contour_orientation,
    'pos': complex_position,
}

def extract_features(contours, extra_features=('area',)):
    """Extracts usual features from contours.

    This function gets a list of contours and for each contour computes the
    centroid position (output x and y)
    Additionally the following features can be extracted (using argument
    `features`)
    """
    # Alternatively if you would like this to be a bit lazier, you could turn
    # this into a generator. To do that, replace the `output.append(features)` in
    # the first loop with a `yield features`. Remove the output initialisation
    # as well, and make sure that none of the functions using the output of this
    # require list specific things and can also work with generators.
    output = []
    for contour in contours:
        # The position is always computed.
        position = contour_centroid(contour)
        features = {
            'x': position[0],
            'y': position[1],
        }
        # Other output features are added by calling callables from constant FEATURES.
        for feature in extra_features:
            features[feature] = FEATURES[feature](contour)
        # Results are appended to he list.
        output.append(features)
    return output
