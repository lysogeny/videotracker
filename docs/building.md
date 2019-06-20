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

To create an executable file, use pyinstaller.

Windows
-------

If you are on Windows, use pyinstaller. A pyinstaller `.spec` file and script
is provided in `devtools/build/windows`. 
To use that `spec` file, check that the `dll_dir` value points to a directory,
where OpenCV's dlls are.

If this is not the case, you need to go find that directory. Typically it is
-ither in `.conda\envs\videotracker\library\bin\`, or another close directory.
If you have a search tool, look for files starting with `opencv_` and ending in
`.dll`.

With the `dll_dir` correctly set, the working directory being
`devtools/build/windows` and `videotracker` being installed, run

    pyinstaller gui.spec

This should create the `videotracker` directory in the `dist` directory. Here
you can find a windows executable.

If you want to create a singular `exe` file, add `--onefile`

    pyinstaller gui.spec --onefile

If you want to do something custom, either manipulate the `gui.spec`, or run pyinstaller
on `gui.py`, and consult the `pyinstaller`
[manual](https://pyinstaller.readthedocs.io/en/stable/) for more information.

It is also further to create a installer bundle for windows using inno setup. A
`.iss` file is included in the Windows build directory.

Mac OS
------

`pyinstaller` will likely work, although is at the moment untested (try the windows `.spec` file, maybe that works).
