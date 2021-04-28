from copy import deepcopy
import pandas as pd
import numpy as np
from Symbolic import DataStructs
from Symbolic import AbstractHelper
from AntlrGrammar.Python3Lexer import Python3Lexer, InputStream
from AntlrGrammar.Python3Parser import Python3Parser
from Symbolic.AbstractConverter import AbstractConverter
from Symbolic.DataStructs import *
from Symbolic.PythonAstVisitor import PythonAstVisitor

'''
    Test cases:
    - Multiple indents on same line (compiler sometimes doesn't think this is an error)
        - eg : if a==10:
                INDENT INDENT print('hi')
    - Half indent - Indent is there but with less spaces (need to figure out whether to push in or out
    - End of a block statement not being a ':', can be possible for long function / conditional definitions
    
'''

def fixIndentation(srcCode, errInfo):
    level = 0
    firstIndent = False
    errLineNo = errInfo.lineNo - 1
    prevLevel = 0
    lastIfLevel = -1
    rCode = deepcopy(srcCode)
    emptyOrCommentLines = set()
    for l, line in enumerate(srcCode.source):
        # if line >= errLine - 1:
        #     break
        inp = InputStream(line)
        lexer = Python3Lexer(inp)
        allTokens = lexer.getAllTokens()
        indentFound = False
        ifFound = False
        if len(allTokens) == 0:
            # Could be a comment or empty line
            indentFound = True
            emptyOrCommentLines.add(l)
        for i, token in enumerate(allTokens):
            if len(allTokens) == 1 and token.type == Python3Parser.NEWLINE:
                # if the line has just a NEWLINE
                indentFound = True
                continue
            if not firstIndent and token.type == Python3Parser.INDENT:
                # first Indent encountered in code get info like whether uses space / tabs and what is indent size
                # TODO: what if first indent itself is incorrect. (Don't think it would create a problem)
                firstIndent = True
                DataStructs.INDENT_SIZE = token.text.count(' ')
                # level += 1
                # indentFound = True
                if DataStructs.INDENT_SIZE == 0:
                    DataStructs.INDENT_SIZE = token.text.count('\t')
                    DataStructs.INDENT_SYMBOL = '\t'

            if token.type == Python3Parser.INDENT:
                # 1 INDENT by ((no_of_spaces_in_indent) / 4) Indents
                indentFound = True
                noOfIndents = token.text.count(DataStructs.INDENT_SYMBOL) // DataStructs.INDENT_SIZE
                floatNoOfIndents = token.text.count(DataStructs.INDENT_SYMBOL) / DataStructs.INDENT_SIZE
                # print(l, len(token.text), floatNoOfIndents)
                if floatNoOfIndents % 1 != 0:
                    # Invalid Indentation (Cases like partial indent, 2 spaces instead of 4 etc.)
                    if l <= errLineNo:
                        prevLevel = level
                        errLineNo = l # Correct this line first
                else:
                    if l == errLineNo:
                        prevLevel = level
                    level = noOfIndents
            elif token.type == Python3Parser.DEDENT:
                # No need to inclue Dedents
                continue
            elif token.type == Python3Parser.IF or token.type == Python3Parser.ELIF:
                ifFound = True

        if not indentFound:
            # no indent found in the current line
            level = 0
        if ifFound:
            if l < errLineNo:
                # NOTE: lt. and not lteq. since we want to consider last encountered if in case the current line is a If line
                lastIfLevel = level

    line = srcCode.source[errLineNo]

    if errLineNo == 0:
        want = 0
    else:
        want = prevLevel
        inp = InputStream(line)
        lexer = Python3Lexer(inp)
        allTokens = lexer.getAllTokens()
        hasElse = False
        hasIf = False
        for token in allTokens:
            if token.type == Python3Parser.IF:
                hasIf = True
            if token.type == Python3Parser.ELIF or token.type == Python3Parser.ELSE:
                hasElse = True
        if hasElse and not hasIf:
            # If current line is an else statement then its indentation should match previous If (elif)
            # TODO: Similar case should be made for try except statements but they are rare
            want = lastIfLevel
        else:
            # Non else case, just take the previous (non empty) lines indentation and guess current lines indentation
            done = False
            prevLine = []
            i = errLineNo - 1
            while i >=0 and not done:
                prevLine = srcCode.source[i]
                if i not in emptyOrCommentLines:
                    done = True
                i -= 1
            if prevLine[-1] == ':':
                want += 1

    prepend = str(DataStructs.INDENT_SYMBOL * want * DataStructs.INDENT_SIZE)
    line = line.lstrip()

    line = prepend + line
    rCode.source[errLineNo] = line
    newErrInfo = rCode.getErrorInfo()

    if checkIndentationError(newErrInfo):
        if newErrInfo.lineNo == errInfo.lineNo:
            #TODO: fix using heuristics (based on error message)
            if 'expected' in newErrInfo.detail:
                oneIndent = DataStructs.INDENT_SIZE * DataStructs.INDENT_SYMBOL
                line = rCode.source[newErrInfo.lineNo - 1]
                line = oneIndent + line
                rCode.source[newErrInfo.lineNo - 1] = line
                tmpErrInfo = rCode.getErrorInfo()
                if not checkIndentationError(tmpErrInfo):
                    fixed = True
                else:
                    # raise Exception("Probably more than one indent required")
                    print("Probably more than one indent required")
                    return None, False
            elif 'unexpected' in newErrInfo.detail:
                # We should be able to fix this with static parsing (above code)
                # raise Exception("Shouldn't have reached here")
                print("Shouldn't have reached here")
                return None, False
            else:
                print("Shouldn't have reached here")
                return None, False
        else:
            rCode, fixed = fixIndentation(rCode, newErrInfo)
    elif newErrInfo.lineNo != -1:
        # print("Still has syntax Errors")
        fixed = True
    else:
        fixed = True

    return rCode, fixed

def fixUsingAntlr(srcCode, errInfo):

    inp = InputStream("\n".join(srcCode.source))
    lexer = Python3Lexer(inp)
    allTokens = lexer.getAllTokens()
    indentFound = False
    for token in allTokens:
        print("{} - {} - {}".format(Python3Parser.symbolicNames[token.type], token.line, len(token.text)))


def checkIndentationError(errInfo):
    if "indentation" in errInfo.errClass.lower() or "tab" in errInfo.errClass.lower():
        return True
    return False

if __name__ == '__main__':

    fromFile = True
    if fromFile:
        code = Code([])
        code.getCodeFromFile("./ExampleScript.py")
        errInfo = code.getErrorInfo()
        # if checkIndentationError(errInfo):
        newCode, fixed = fixIndentation(code, errInfo)
        if not fixed:
            print("not fixed")
        else:
            for line in newCode.source:
                print(line)
    else:
        filename = '../data/Python CEs/SingleIndentationErrors.csv'
        df = pd.read_csv(filename)
        print("total size", df.shape)
        identErrors = 0
        fixed = 0
        for i, row in df.iterrows():
            srcLine = str(df.iloc[i]['sourceText'])
            code = Code(srcLine)
            errInfo = code.getErrorInfo()
            if checkIndentationError(errInfo):
                identErrors += 1
                newCode, fixedIt = fixIndentation(code, errInfo)
                if fixedIt and newCode.getErrorInfo().lineNo == -1:
                    print("completely fixed")
                if not fixedIt:
                    print("not fixed", i)
                else:
                    fixed += 1
                # for line in newCode.source:
                #     print(line)
        print(identErrors)
        print("fixed", fixed)
