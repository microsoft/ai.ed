# Getting started with Python Tutor

This project consists of two components:

1. A repair engine. Currently, we are relying on **PyMACER** as a repair engine, which is a Python adaptation of [MACER: A Modular Framework for Accelerated Compilation Error Repair.](https://arxiv.org/abs/2005.14015). Before starting, you will need to clone the `PyMACER` repo from [here](https://github.com/purushottamkar/pymacer).
2. **pytutor** provides the front-end experience of python tutor in VS code.

## Pre-requisities

- Python [3.8.9 (64-bit)](https://www.python.org/downloads/release/python-389/). Python 3.9 does not work due to tensorflow requirement.
- Visual Studio 2019 with Desktop development with C++.
- VS Code.
- [`node`](https://treehouse.github.io/installation-guides/windows/node-windows.html) version 14.17.0 and `npm` version 6.14.13 for building the VSCode extension `pytutor`.

## PyMACER

PyMACER uses the edlib package, which wraps a C++ library. This package does not have pre-built Windows binaries ([Issue #178: Binary wheels for Windows](https://github.com/Martinsos/edlib/issues/178)), so you will need to build from source during `pip install`. To prepare for this, verify that you have the [Desktop development with C++](https://docs.microsoft.com/en-us/cpp/build/vscpp-step-0-installation?view=msvc-160) workload selected in the [Visual Studio 2019 installer](https://docs.microsoft.com/en-us/visualstudio/install/modify-visual-studio?view=vs-2019).

Then, execute the following commands using the [x64 Native Tools Command Prompt for VS 2019](https://docs.microsoft.com/en-us/cpp/build/how-to-enable-a-64-bit-visual-cpp-toolset-on-the-command-line?view=msvc-160) so that Python will have access to the required C++ build tools. The first line will clone the pymacer
repo to `C:\pymacer` and move required server-related files there. The next lines will 
create a virtual environment for Python, activate it, and then install the
requirements, and start the pymacer server.

```
git clone https://github.com/purushottamkar/pymacer C:\pymacer
copy .\src\pymacer_server.py C:\pymacer\pymacer-vscode\
python -m venv C:\pymacer\venv
C:\pymacer\venv\Scripts\activate
cd C:\pymacer\pymacer-vscode\
python -m pip install -r requirements.txt
python pymacer_server.py
```
You may see some error messages saying `ERROR: After October 2020 you may experience ...` and some expected warnings related to TensorFlow. You can ignore those. 
Upon successful deployment of the server, the last two lines should display:

```
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## pytutor

The PyMACER server should already be running before using the extension. 
Open a new terminal and change your directory to `src/pytutor`. 
Then execute `npm install` to install the required npm packages. 
Then execute `code .` to open the project using VS Code.

Click the `Run and Debug (Ctrl+Shift+D)` button on the left toolbar. 
Then click `Run Extension` from the top toolbar to initiate a separate instance of VS code with the extension enabled.

Create a new python file or open an existing one. You can verify that the `Python Tutor` extension has loaded by the information message in the bottom right of VS Code saying: Python Tutor: Beginner Mode Activated 👩‍🎓.
