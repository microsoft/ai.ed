import ast
from Symbolic import DataStructs
from Symbolic import AbstractHelper
from AntlrGrammar.Python3Lexer import Python3Lexer, InputStream
from AntlrGrammar.Python3Parser import Python3Parser
from Symbolic.DataStructs import *
from Symbolic.PythonAstVisitor import PythonAstVisitor
from timeit import default_timer as timer

from Symbolic.SymbTable import SymbTable


class AbstractConverter:

    def __init__(self, sourceCode, inferTypes=True, debug=True, useAST=True):
        self.sourceCode = sourceCode
        # self.truncatedCode = sourceCode # Code truncated at error line
        self.tokenizedCode = None
        self.abstractCode = None
        self.useAST = useAST
        self.debug = debug
        self.inferTypes = inferTypes

    '''
        Method tokenizes the self.sourceCode using Antlr generated Python3Lexer. Also uses PythonAstVisitor for basic
        Type inference. Returns the tokenizedCode as a list of list of TokenAntlr Objects 
        and also saves it. Also returns symbol table.
    '''
    def getTokenizedCodeAntlr(self):
        start = timer()
        symbTable = SymbTable(debug=self.debug)

        if self.useAST:
            # Code shouldn't have errors for ast to be generated so truncate the source code from first error line
            truncatedCode = AbstractHelper.truncateAtErrLine(self.sourceCode)

            pyVisitor = PythonAstVisitor(symbTable, inferTypes=self.inferTypes, debug=self.debug)
            tree = ast.parse("\n".join(truncatedCode.source))
            pyVisitor.visit(tree)  # This fills in the symbTable also does some basic type inference

        tokenizedCode = []
        firstIndent = False
        currScope = 'global'
        level = 0
        for l, line in enumerate(self.sourceCode.source):
            tmp_list = []
            inp = InputStream(line)
            lexer = Python3Lexer(inp)
            allTokens = lexer.getAllTokens()
            tmpLvl, tmpScope = symbTable.getLevelAndScope(l + 1)
            if tmpLvl != -1:
                level, currScope = tmpLvl, tmpScope
            for i, token in enumerate(allTokens):
                if token.type == Python3Parser.NEWLINE and len(allTokens) != 1:
                    continue
                if not firstIndent and token.type == Python3Parser.INDENT:
                    firstIndent = True
                    DataStructs.INDENT_SIZE = token.text.count(' ')
                    if DataStructs.INDENT_SIZE == 0:
                        DataStructs.INDENT_SIZE = token.text.count('\t')
                        DataStructs.INDENT_SYMBOL = '\t'
                if token.type == Python3Parser.INDENT:
                    # Replace 1 INDENT by ((no_of_spaces_in_indent) / 4) Indents
                    symb_name = AbstractHelper.getTokenSymbName(token, allTokens, symbTable, i, l + 1, level, currScope)
                    noOfIndents = token.text.count(DataStructs.INDENT_SYMBOL) // DataStructs.INDENT_SIZE
                    if noOfIndents == 0:
                        # TODO: Invalid Indentation
                        noOfIndents = 1
                    indentText = DataStructs.INDENT_SYMBOL * DataStructs.INDENT_SIZE
                    column = 0
                    for i in range(noOfIndents):
                        myToken = TokenAntlr(token.type, token.line, column, indentText, symb_name)
                        column += len(indentText)
                        tmp_list.append(myToken)
                elif token.type == Python3Parser.DEDENT:
                    # No need to include Dedents in abstraction
                    continue
                else:
                    symb_name = AbstractHelper.getTokenSymbName(token, allTokens, symbTable, i, l + 1, level, currScope)
                    tokenText = token.text
                    if token.type == Python3Parser.NEWLINE:
                        # need to handle as by default it takes the previous token text
                        tokenText = '\n'
                    elif token.type == Python3Parser.DEDENT:
                        # need to handle as by default it takes the previous token text
                        tokenText = ''
                    myToken = TokenAntlr(token.type, token.line, token.column, tokenText, symb_name)
                    tmp_list.append(myToken)

            tokenizedCode.append(tmp_list)

        if self.debug:
            print("tokenize time", timer() - start)
        self.tokenizedCode = tokenizedCode
        return self.tokenizedCode, symbTable

    '''
        Method returns abstract code, tokenizedCode and symbTable as a list of list of strings. Abstract code is different from
        tokenized code as it contains just the abs_name of tokens as a string.
    '''
    def getAbstractionAntlr(self):
        '''
        Method returns abstract code, tokenizedCode and symbTable as a list of list of strings. Abstract code is different from
        tokenized code as it contains just the abs_name of tokens as a string.
        :return:
        '''
        # if self.abstractCode is None:
        self.tokenizedCode, symbTable = self.getTokenizedCodeAntlr()
        self.abstractCode = AbstractHelper.getAbstractCodeFromTokenizedCode(self.tokenizedCode)
        return self.tokenizedCode, self.abstractCode, symbTable
