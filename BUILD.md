# Building the Project

This project consists of two components:

1. PyMACER. PyMACER is a Python adaptation of [MACER: A Modular Framework for Accelerated Compilation Error Repair.](https://github.com/purushottamkar/macer).
2. vscode-extension. This provides the frontend experience in Visual Studio Code, and uses PyMACER.

Both of these components are found in the `ai-compile` directory.

## Pre-requisities

- Python 3.8.9 (64-bit). Python 3.9 does not work due to tensorflow requirement.
- Visual Studio 2019 with Desktop development with C++.
- Some recent version of node and npm for building the vscode-extension.

## PyMACER

PyMACER uses the edlib package, which wraps a C++ library. This package does not have pre-built Windows binaries ([Issue #178: Binary wheels for Windows](https://github.com/Martinsos/edlib/issues/178)), so you will need to be built from source during `pip install`. To prepare for this, verify that you have the "Desktop development with C++" workload selected in the Visual Studio 2019 installer.

Then, perform the following commands using the `x64 Native Tools Command Prompt for VS 2019` command prompt so that Python will have access to the required C++ build tools.

Create a virtual environment for Python. Here, we'll assume this environment will be located `C:\venv\pymacer`.

```
python -m venv C:\venv\pymacer
C:\venv\pymacer\Scripts\activate
python -m pip install -r requirements.txt
```

After installation, you should be able to start the server with:

```
python server.py
```

This will display some expected warnings related to TensorFlow. The last lines should display:

```
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

You can test the REST server by sending a `POST` request to `http://localhost:5000/getfixes` with your favorite client:

```json
{
  "source": "number = str(input(\"Enter a number\"))\r\nprint(\"You chose \" number)",
  "lastEditLine": 9
}
```

The response should have some useful data.

## vscode-extension

The PyMACER server should already be running before using this extension.

Within the `vscode-extension` directory, type `npm install` to install the required npm packages. Then:

```
code .
```

Click the `Run and Debug` button on the left toolbar. Then click `Run Extension` to run the extension.

After opening a Python file, you can verify that the extension has loaded in the debug console:

```
Extension 'python-hints' is now active!
```
