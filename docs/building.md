Building
========

This file describes steps for either installing this software through your
package manager or creating an executable file (`videotracker.exe`,
`videotracker`) that bundles the dependencies.

Generally, if you have a development environment and would just like to use
this software on that computer, just running `python setup.py install` should
install this.

GNU/Linux
---------

If you are on Arch Linux, use one of the `PKGBUILD` files in the `devtools/`
directory to create a pacman package.

Windows
-------

If you are on Windows, use either py2exe or pyinstaller.

Mac OS
------

`pyinstaller` will likely work.
