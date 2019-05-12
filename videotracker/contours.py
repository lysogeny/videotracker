"""Tools for contours"""

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
    centre = (
        int(moments['m10']/moments['m00']),
        int(moments['m01']/moments['m00'])
    )
    return centre

def extract_features(contours):
    """Extracts usual features from contours"""
    output = []
    for contour in contours:
        position = contour_centroid(contour)
        features = {
            'x': position[0],
            'y': position[1],
            'area': cv2.contourArea(contour),
            'orientation': None,
            'mean_value': None,
        }
        output.append(features)
    return output
