Installing a development environment
====================================

To install a development environment for videotracker, you need:

- PyQt5
- python≥3.7
- OpenCV≥4.0.0

You can go about acquiring these in several ways, below are some of the ways
that have worked for me.

Windows
-------

On windows install anaconda, miniconda or something similar.

Then create an environment:

    conda create -n videotracker python=3.7

Activate that environment:

    conda activate videotracker

Install OpenCV (feel free to try 4.0.0 or other versions):

    conda install -c conda-forge opencv=4.1.0

Install PyQt5:

    pip install pyqt5


GNU/Linux
---------

The best way of installing these dependencies on GNU/Linux is through your
package manager (`apt`, `yum`, `pacman`, `emerge`, ...). 

If your system's package manager can get you the appropriate versions of
packages, I suggest that you use that. For instance:

    pacman -S opencv python-pyqt5 python

Should get you the necessary packages on Arch Linux.

This method has a couple of downfalls. Depending on your Linux distro, some
packages might be outdated or just missing. Maybe you need two different
versions of OpenCV, your system likely will handle only one.
If your distribution does not provide you with packages that you can
use, or you need multiple OpenCV installs perform the steps described in the
following steps.

### Anaconda

Install `miniconda3`, `anaconda`, or something else that provides conda.

Create a new environment:

    conda create -n videotracker python>=3.7

Activate the environment:

    conda activate videotracker

Install OpenCV:

    conda install -c conda-forge opencv>=4.1.0

Install PyQt5:

    pip install pyqt5

This should work, but is currently untested.
Note that this is not the only way of installing the dependencies using on
Linux.

Mac OS
------

The steps for Mac OS are the same as for Windows and Linux.

Verify working libraries 
------------------------

If you have done the OS specific steps above, go and see if the environment
works as expected. The simplest way is to just run videotracker in the
environment, but if you wish to check that individual components work, the
following steps should allow you to figure out if it is working.
The examples are written using `ipython`, If you don't have `ipython`, you can
also use `python`, or just install `ipython` with one of the usual means
(`conda install ipython`, `pip install ipython` or whatever means your system might
provide (`apt`, `yum`, `brew`, `pacman`, `emerge`, ...)).

### OpenCV

Check that OpenCV has the correct version and works:

    > ipython
    In [1]: import cv2

    In [2]: cv2.__version__
    Out[2]: '4.1.0'

As long as you get ≥4.0.0 and don't run into an `ImportError` OpenCV will likely work.
Still, you should check that videofiles can be read:

    In [3]: cap = cv2.VideoCapture('file.mp4')

    In [4]: cap.read()
    Out[4]: 
    (True, array([[[...]]])

If the first value in `Out[4]` is `True`, VideoCapture works.

### PyQt5

To check that PyQt5 works, run the following:

    > ipython
    In [1]: from PyQt5 import QtWidgets

    In [2]: app = QtWidgets.QApplication([])

    In [3]: widget = QtWidgets.QSpinBox()

    In [4]: widget.show()

    In [5]: app.exec_()

This should spawn a window with a singular [spin box](https://en.wikipedia.org/wiki/Spinner%5F%28computing%29).
If any of the steps in between have caused an error, or no spin box is shown, something went wrong.
