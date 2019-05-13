Video tracker
=============

Modular video tracker offering a Qt5 GUI.

The segmentation method is intended to be easily replaced, offering modularity.


Feature list
------------

- [ ] Segmentation Modules
    - [x] Adaptive threshold segmentation
    - [ ] threshold segmentation
    - [ ] MOG2 background subtractor segmentation
    - [ ] Optical flow tracking
    - [ ] Other methods?
- [x] Display polygons
- [x] Display other frames
- [x] CSV output
- [x] Video output
- [x] Running tracking
- [ ] Connecting tracked objects to form paths
- [ ] Diagnostics plots
- [ ] Packaging
    - [ ] Windows
    - [ ] Mac OS
    - [ ] Debian
    - [x] Archlinux
- [x] Command line argument parsing
- [x] Video view
- [x] Opening videos
- [x] Panning through videos
- [x] Zoom in videos
- [x] Some kind of a GUI
- [ ] Batch mode

Bugs
----

- [ ] After completion state is not reset to not running
- [ ] Video and csv outputs are not automatically set when checking boxes.
- [ ] File... buttons are not disabled when running
- [ ] Option load... is not disabled when running
- [ ] Play button not connected to start
- [ ] Single frame previews are slow
- [ ] Preview checkbox does nothing
- [ ] `video.frames` is wrong (mismatch in actual maximum frames and frames).
- [ ] Output polygon colour is red while video polygon colour is blue
- [ ] Current file name is not displayd anywhere
- [ ] Video and csv output files are not reset when new file is loaded.


Minor features
--------------

- [x] KeyboardInterrupt 
- [ ] Colour choices for output polygon tracking thing
- [ ] Hypermodular segmentation modules: combine all of your favourite cv2 functions into a method.


Requirements
------------

- python3
- PyQt5
- OpenCV>=3


License
-------

This is software that I wrote working for the state of
[Baden-Württemberg](https://en.wikipedia.org/wiki/Baden-W%C3%BCrttemberg). 
As such, it is funded (at least to some extent) by tax money. In the interest
of reproducibility and the idea of ["public money public code"](https://publiccode.eu/), 
I am releasing this under the [MIT license](https://en.wikipedia.org/wiki/MIT_License) 
(See also LICENSE).

