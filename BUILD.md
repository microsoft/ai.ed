# Getting started

This project consists of two components:

1. A repair engine. Currently, we are relying on **PyMACER** as a repair engine, which is a Python adaptation of [MACER: A Modular Framework for Accelerated Compilation Error Repair.](https://github.com/purushottamkar/macer). `PyMACER` is *NOT* part
of Microsoft and will be moved out of this repo.
2. **vscode-extension** provides the front-end experience of python tutor in VS code.

Both of these components are in the `ai-compile` directory.

## Pre-requisities

- Python [3.8.9 (64-bit)](https://www.python.org/downloads/release/python-389/). Python 3.9 does not work due to tensorflow requirement.
- Visual Studio 2019 with Desktop development with C++.
- [`node`](https://treehouse.github.io/installation-guides/windows/node-windows.html) version 14.17.0 and `npm` version 6.14.13 for building the vscode-extension.

## PyMACER

PyMACER uses the edlib package, which wraps a C++ library. This package does not have pre-built Windows binaries ([Issue #178: Binary wheels for Windows](https://github.com/Martinsos/edlib/issues/178)), so you will need to build from source during `pip install`. To prepare for this, verify that you have the [Desktop development with C++](https://docs.microsoft.com/en-us/cpp/build/vscpp-step-0-installation?view=msvc-160) workload selected in the [Visual Studio 2019 installer](https://docs.microsoft.com/en-us/visualstudio/install/modify-visual-studio?view=vs-2019).

Then, execute the following commands using the [x64 Native Tools Command Prompt for VS 2019](https://docs.microsoft.com/en-us/cpp/build/how-to-enable-a-64-bit-visual-cpp-toolset-on-the-command-line?view=msvc-160) so that Python will have access to the required C++ build tools. The first line will create a virtual environment for Python. Here, we will assume this environment will be located in `C:\venv\pymacer`. Change your current directory to `ai-compile\PyMacer` before executing the commands.

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

The PyMACER server should already be running before using this extension. Open another [x64 Native Tools Command Prompt for VS 2019](https://docs.microsoft.com/en-us/cpp/build/how-to-enable-a-64-bit-visual-cpp-toolset-on-the-command-line?view=msvc-160) window. Then change your current directory to `vscode-extension`.

Open a new terminal and change your directory to `vscode-extension`. Then execute `npm install` to install the required npm packages. Then execute the
following command:

```
code .
```

Click the `Run and Debug (Ctrl+Shift+D)` button on the left toolbar. Then click `Run Extension` from the top toolbar to initiate a separate instance of VS code with the extension enabled.

Create a new python file or open an existing one. You might 
need to install a python debugger extension.  After opening a Python file, you can verify that the `python-hint` extension has loaded in the debug console of the first instance of VS code:

```
Extension 'python-hints' is now active!
```
