from Symbolic.DataStructs import *
from AntlrGrammar.Python3Parser import Python3Parser

'''
    Utility Method returns Abstract line given a tokenized line (list of TokenAntlr)
'''
def getAbstractLineFromTokenizedLine(tokenizedLine):
    tmp_list = []
    for token in tokenizedLine:
        tmp_list.append(token.symb_name)
    return tmp_list

'''
    Utility Method returns Abstract Code given a tokenized code (list of list of TokenAntlr)
'''
def getAbstractCodeFromTokenizedCode(tokenizedCode):
    abstractCode = []
    for line in tokenizedCode:
        abstractCode.append(getAbstractLineFromTokenizedLine(line))
    return abstractCode

'''
    Utility Method returns plain(original) line given a tokenized line (list of TokenAntlr)
'''
def getPlainLineFromTokenizedLine(tokenizedLine):
    tmp_line = []
    for token in tokenizedLine:
        tmp_line.append(token.text)
    return tmp_line

'''
    Utility Method returns plain(original) code given a tokenized code (list of list of TokenAntlr)
'''
def getPlainCodeFromTokenizedCode(tokenizedCode):
    plainCode = []
    for line in tokenizedCode:
        plainCode.append(getPlainLineFromTokenizedLine(line))
    return plainCode

'''
    Utility Method to truncate a source code at given line. If lineNo is not given or is None then it truncates the code
    at first error line. Recursively truncates the code till remaining code has no errors remaining.
'''
def truncateAtErrLine(code, lineNo=None):
    truncatedCode = code
    if lineNo is None:
        errInfo = code.getErrorInfo()
        lineNo = int(errInfo.lineNo)

    if lineNo != -1:
        # print('truncated', lineNo)
        truncatedCode = code.source[:(lineNo - 1)]
        truncatedCode = Code(truncatedCode)
        newLineNo = truncatedCode.getErrorInfo().lineNo
        if newLineNo > -1:
            truncatedCode = truncateAtErrLine(truncatedCode, newLineNo)  # recursively truncate till error exits

    return truncatedCode

'''
    Utility method given a token (TokenAntlr object), symbTable and lineNo returns the abstract representation of 
    token.text. SymbTable is used only when the token is of type NAME (Mainly Var, function, class)
'''
def getTokenSymbName(token, allTokens, symbTable, i, lineNo, level, currScope):
    typeStr = Python3Parser.symbolicNames[token.type]
    if token.text in BUILT_IN_FUNC or token.text in SPECIALS:
        typeStr = token.text
    elif typeStr == "NAME":
        currLine = lineNo
        value = symbTable.getSymbAtLineNo(token.text, currLine)
        if value is not None:
            typeStr = value["abs_name"]
        else:
            if i > 1 and allTokens[i-1].text == "." and allTokens[i-2].type == Python3Parser.NAME:
                # Its a class attribute
                objName = allTokens[i-2].text
                searchText = objName + "." + token.text
                value = symbTable.getSymbAtLineNo(searchText, currLine)
                if value is not None:
                    typeStr = value["abs_name"]
                else:
                    prefixSymb = symbTable.getLatestSymbFromSymTable(searchText, currLine, currScope, level)
                    if prefixSymb != "-1":
                        typeStr = prefixSymb
            else:
                prefixSymb = symbTable.getLatestSymbFromSymTable(token.text, currLine, currScope, level)
                if prefixSymb != "-1":
                    typeStr = prefixSymb
    return typeStr
