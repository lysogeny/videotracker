Video tracker
=============

Modular video tracker offering a Qt5 GUI.

The segmentation method is intended to be easily replaced, offering modularity.


Feature list
------------

- [ ] Segmentation Modules
    - [ ] Adaptive threshold segmentation
    - [ ] threshold segmentation
    - [ ] MOG2 background subtractor segmentation
    - [ ] Optical flow tracking
    - [ ] Other methods?
- [ ] CSV output
- [ ] Video output
- [ ] Running tracking
- [ ] Connecting tracked objects to form paths
- [ ] Diagnostics plots
- [ ] Packaging for windows
- [ ] Packaging for mac OS
- [x] Video view
- [x] Opening videos
- [x] Panning through videos
- [x] Zoom in videos
- [x] Some kind of a GUI


Requirements
------------

- python3
- PyQt5
- OpenCV (currently 4, 3, maybe 2 will work. I am working with opencv4)


License
-------

This is software that I wrote working for the state of
[Baden-Württemberg](https://en.wikipedia.org/wiki/Baden-W%C3%BCrttemberg). 
As such, it is funded (at least to some extent) by tax money. In the interest
of reproducibility and the idea of ["public money public code"](https://publiccode.eu/), 
I am releasing this under the [MIT license](https://en.wikipedia.org/wiki/MIT_License) 
(See also LICENSE).

