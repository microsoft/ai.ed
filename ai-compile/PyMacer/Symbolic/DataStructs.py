import os
import sys
import tokenize
import traceback
from copy import deepcopy
from token import tok_name
from io import BytesIO, StringIO
import code as cd
import re

from Common import utils
from ML import Globals
from timeit import default_timer as timer
KEYWORDS = {"await", "else", "import", "pass", "break", "except", "in", "raise", "class",
            "finally", "is", "return", "and", "continue", "for", "lambda", "try", "as", "def", "from", "nonlocal",
            "while", "assert", "del", "global", "not", "with", "async", "elif", "if", "or", "yield"}

SPECIALS = {"self"}

BUILT_IN_FUNC = {"abs", "delattr", "hash", "memoryview", "set", "all", "dict", "help", "min", "setattr", "any", "dir",
                 "hex", "next", "slice", "ascii", "divmod", "id", "object", "sorted", "bin", "enumerate", "input",
                 "oct", "staticmethod", "bool", "eval", "int", "open", "str", "breakpoint", "exec", "isinstance",
                 "ord", "sum", "bytearray", "filter", "issubclass", "pow", "super", "bytes", "float", "iter", "print",
                 "tuple", "callable", "format", "len", "property", "type", "chr", "frozenset", "list", "range", "vars",
                 "classmethod", "getattr", "locals", "repr", "zip", "compile", "globals", "map", "reversed",
                 "__import__", "complex", "hasattr", "max", "round"}

INDENT_SYMBOL = ' '
INDENT_SIZE = 4

class ErrInfo:

    def __init__(self, errClass, detail, lineNo):
        self.errClass = errClass
        self.detail = detail
        self.lineNo = lineNo

    def __str__(self):
        return "{} : {} -> {}".format(self.errClass, self.lineNo, self.detail)

    def getAbs(self):
        msg = str(self.errClass) + ": " + str(self.detail)
        msg = re.sub(r'\'(.*?)\'', 'ID', msg)
        msg = re.sub('\d+', 'NUM', msg)
        return msg

    def findIDs(self):
        patternStr = r'([^\']*?)\'(.*?)\'([^\']*?)'
        ids = []
        matches = re.findall(patternStr, self.detail)
        for match in matches:
            ids.append(match[1])
        return ids


class Code:
    def __init__(self, source, codeID='-1'):
        if isinstance(source, list):
            self.source = source
        elif isinstance(source, str):
            self.source = source.splitlines()
        self.codeID = codeID
        self.errInfo = None

    def getCodeFromFile(self, filePath):
        with open(filePath, "r") as file:
            lines = file.readlines()
            tmpSource = []
            for line in lines:
                tmp_line = line
                if tmp_line[-1] == '\n':
                    tmp_line = tmp_line[:-1]
                tmpSource.append(tmp_line)
            self.source = tmpSource

    def getErrorInfo(self, fromFile=False):
        if self.errInfo is None:
            try:
                Globals.compile_freq += 1
                start = timer()
                compile("\n".join(self.source), filename='../tmp/temp.py', mode='exec')
                Globals.compile_time += timer() - start

                # if fromFile:
                    # exec("\n".join(self.source))
                #     compile("".join(self.source), filename='temp.py', mode='exec')
                # else:
                #     compile("\n".join(self.source), filename='temp.py', mode='exec')
                    # exec("".join(self.source))
            except SyntaxError as err:
                error_class = err.__class__.__name__
                detail = err.args[0]
                line_number = int(err.lineno)
            except Exception as err:
                error_class = err.__class__.__name__
                detail = err.args[0]
                cl, exc, tb = sys.exc_info()
                line_number = int(traceback.extract_tb(tb)[-1][1])
            else:
                # print("No error in code")
                error_class = "No Error"
                detail = ""
                line_number = -1

            self.errInfo = ErrInfo(error_class, detail, line_number)
        return self.errInfo

    def __deepcopy__(self, memodict={}):
        newCode = Code('')
        newCode.source = deepcopy(self.source)
        return newCode


class TokenAntlr:

    def __init__(self, type, line, column, text, symb_name):
        self.type = type
        self.line = line
        self.column = column
        self.text = text
        self.symb_name = symb_name

    def __str__(self):
        return "{}, {}-{}, {}".format(self.type, self.line, self.column, self.text, self.symb_name)


class EditDiff:

    def __init__(self, editType, start, end, tokenStr=''):
        self.editType = editType
        self.start = start
        self.end = end
        self.tokenStr = tokenStr

class Feedback:

    def __init__(self, fullText, msg1, msg2, actionMsg, action, tokens, tokensText, misc):
        self.fullText = fullText
        self.msg1 = msg1
        self.msg2 = msg2
        self.actionMsg = actionMsg
        self.action = action
        self.tokens = tokens
        self.tokensText = tokensText
        self.misc = misc

    def __str__(self):
        return self.fullText
#
# class Token:
#
#     def __init__(self, exact_type, typeStr, start, end, text, line, dataType=None):
#         self.exact_type = exact_type
#         self.typeStr = typeStr
#         self.start = start
#         self.end = end
#         self.text = text
#         self.line = line
#         self.dataType = dataType
#
#     def __str__(self):
#         # return "{} : {} - {} : {}; line : {}".format(self.typeStr, self.start, self.end,
#         #                                              self.text if self.text != '\n' else "nl",
#         #                                              self.line)
#         return "{} : {} - {} : {}".format(self.typeStr, self.start, self.end,
#                                           self.text if self.text != '\n' else "nl")

### Code to use Intercative Console
# console = cd.InteractiveConsole()
#         console.push("from utils import parseGlobals")
#         currLine = 0
#         globalsDict = {}
#         absNameFull = []
#         for line in sourceCode.source:
#             old_stdout = sys.stdout
#             sys.stdout = StringIO()
#             absLine = abstractCode[currLine]
#             try:
#                 rval = console.push(line)
#                 absNames = list(map(lambda tok: tok.typeStr, absLine))
#                 absNameFull.append(absNames)
#                 if "NAME" in absNames:
#                     Indent = 0
#                     if rval:
#                         Indent = 1
#                     # console.push("parseGlobals(globals())")
#                     appendVal = sys.stdout.getvalue().strip()
#                     if appendVal != '':
#                         globalsDict[currLine] = appendVal
#             except Exception as e:
#                 print(e)
#             finally:  # !
#                 sys.stdout = old_stdout  # !
#                 currLine += 1
#         print(sourceCode.source)
# print(absNameFull)
# for k,v in globalsDict.items():
#     print("{} -> {}".format(k,v))
