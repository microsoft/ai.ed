# Getting started

The project consists of two components:

1. **PyMACER** is a Python adaptation of [MACER: A Modular Framework for Accelerated Compilation Error Repair.](https://github.com/purushottamkar/macer).
2. **vscode-extension** provides the front-end experience pf PyMACER in Visual Studio Code.

Both of these components are in the `ai-compile` directory.

## Pre-requisities

- Python [3.8.9 (64-bit)](https://www.python.org/downloads/release/python-389/). Python 3.9 does not work due to tensorflow requirement.
- Visual Studio 2019 with Desktop development with C++.
- [`node`](https://treehouse.github.io/installation-guides/windows/node-windows.html) version 14.17.0 and `npm` version 6.14.13 for building the vscode-extension.

## PyMACER

PyMACER uses the edlib package, which wraps a C++ library. This package does not have pre-built Windows binaries ([Issue #178: Binary wheels for Windows](https://github.com/Martinsos/edlib/issues/178)), so you will need to build from source during `pip install`. To prepare for this, verify that you have the "Desktop development with C++" workload selected in the Visual Studio 2019 installer.

Then, perform the following commands using the `x64 Native Tools Command Prompt for VS 2019` command prompt so that Python will have access to the required C++ build tools.

Create a virtual environment for Python. Here, we'll assume this environment will be located `C:\venv\pymacer`.

```
python -m venv C:\venv\pymacer
C:\venv\pymacer\Scripts\activate
python -m pip install -r requirements.txt
```
You may see some error messages saying `ERROR: After October 2020 you may experience ...`. You can ignore that. 

After installation, start the server with:

```
python server.py
```

This will display some expected warnings related to TensorFlow. The last lines should display:

```
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## vscode-extension

The PyMACER server should already be running before using this extension.

Open a new terminal and change your directory to `vscode-extension`. Then execute `npm install` to install the required npm packages. Then execute the
following command:

```
code .
```

Click the `Run and Debug` button (Ctrl+Shift+D) on the left toolbar. Then click `Run Extension` to run the extension.

After opening a Python file, you can verify that the extension has loaded in the debug console:

```
Extension 'python-hints' is now active!
```
