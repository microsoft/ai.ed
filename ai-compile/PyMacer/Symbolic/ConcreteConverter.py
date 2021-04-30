from copy import deepcopy
import pandas as pd

import Symbolic.AbstractConverter
from Symbolic.AbstractConverter import AbstractConverter
from Symbolic import  AbstractHelper
from Symbolic import CigarSrcTrgt
from Symbolic import ConcreteHelper
from Symbolic import ConcreteToken
from Symbolic.DataStructs import *
from tokenize import *


class ConcreteConverter:

    def __init__(self, abstractLine, tokenizedCode=None, debug=True):
        self.tokenizedCode = tokenizedCode
        self.abstractLine = abstractLine
        self.debug = debug

    '''
    Tries to convert the self.abstractCode to Concretized code using srcTokenizedCode. if self.tokenizedCode is None 
    symbTable is mandatory argument else raises an Exception. if self.tokenizedCode is not None, uses it directly to 
    concretize the code (However we would never have tokenizedCode for real world examples).
    '''

    def getConcreteLine(self, srcTokenizedCode, lineNo, symbTable=None):
        isConcretized = False
        concreteLine = None
        if self.tokenizedCode is not None:
            line = self.tokenizedCode[lineNo - 1]

            tmp_line = []
            for token in line:
                if token.text != '':
                    tmp_line.append(token.text)
            concreteLine = tmp_line
            isConcretized = True  # If we have tokenized code (#NEVER_HAPPENS) its easy and guaranteed to be concretized

        elif self.abstractLine is not None:
            if lineNo is None or symbTable is None:
                raise Exception("Need symbTable or tokenized code to concretize")
            tgtAbsLine = self.abstractLine # [lineNo - 1]

            srcLine = AbstractHelper.getPlainLineFromTokenizedLine(srcTokenizedCode[lineNo - 1])
            srcAbsLine = AbstractHelper.getAbstractLineFromTokenizedLine(srcTokenizedCode[lineNo - 1])
            cigar = CigarSrcTrgt.lineUp_SrcTrgAbs(srcAbsLine, tgtAbsLine)
            if self.debug:
                print("Cigar", cigar)

            srcTrgtCigar = CigarSrcTrgt.CST_Params(-1, srcLine, srcAbsLine, tgtAbsLine, cigar, symbTable)
            isConcretized = ConcreteHelper.concretizeLine(srcTrgtCigar, lineNo)
            concreteLine = srcTrgtCigar.trgtLine
            if self.debug:
                print("trgt line ", srcTrgtCigar.trgtLine, isConcretized)

        return concreteLine, isConcretized


def attemptConcretization(srcCodeObj, srcTokenizedCode, symbTable, predAbsLine, lineNo, debug=True, inferTypes=True):
    try:
        concreteConverter = ConcreteConverter(predAbsLine, debug=debug)
        # abstractCoverter = AbstractConverter(sourceCode=srcCodeObj, debug=debug, inferTypes=inferTypes)
        # srcTokenizedCode, srcAbstractCode, symbTable = abstractCoverter.getAbstractionAntlr()
        concreteLine, isConcretized = concreteConverter.getConcreteLine(srcTokenizedCode, lineNo, symbTable)


        return concreteLine, isConcretized

    # If not possible, note down the failure cases
    except Exception as e:
        exception = repr(e)
        if lineNo > 0:
            traceback.print_exc()
            print('During exception Line num ', lineNo)
        return exception, False

'''
    Utility Method not to be used in MACER/MACER++ pipeline. Just for testing.
'''
def generateArtificialError(abstractCode, editLineNo, typeEdit, editColNo, token):
    tgtAbsCode = deepcopy(abstractCode)
    if typeEdit == 'insert':
        tgtAbsCode[editLineNo - 1].insert(editColNo, token)
    elif typeEdit == 'replace':
        tgtAbsCode[editLineNo - 1][editColNo] = token
    elif typeEdit == 'delete':
        tmp_line = []
        for i, token in enumerate(tgtAbsCode[editLineNo - 1]):
            if i == editColNo:
                continue
            tmp_line.append(token)
        tgtAbsCode[editLineNo - 1] = tmp_line

    return tgtAbsCode


if __name__ == '__main__':
    fromFile = False
    if fromFile:
        code = Code([])
        code.getCodeFromFile("./ExampleScript.py")
    else:
        filename = '../data/Python CEs/newZeroLine.csv'
        df = pd.read_csv(filename)
        srcLine = df.iloc[284]['sourceText']
        print(srcLine)
        srcLine = srcLine.split("\n")

        code = Code(srcLine)
    abstractCoverter = AbstractConverter(code, inferTypes=True, debug=False)
    # srcTokenizedCode, symbTable = abstractCoverter.getTokenizedCodeAntlr()
    srcTokenizedCode, abstractCode, symbTable = abstractCoverter.getAbstractionAntlr()
    print(code.getErrorInfo())
    # for line in srcTokenizedCode:
    #     print([str(token.text) + "->" +str(token.symb_name) for token in line])
    for line in abstractCode:
        print([str(token) for token in line])
    # symbTable.printSymbTable()
    # exit()
    ##############################
    # editLineNo = code.getErrorInfo().lineNo
    # typeEdit = 'insert'
    # editColNo = 0
    # token = 'NAME'
    # tgtAbsCode = generateArtificialError(abstractCode, editLineNo, typeEdit, editColNo, token)
    # print(tgtAbsCode[editLineNo - 1])
    # ################################
    #
    # concreteConverter = ConcreteConverter(abstractCode=tgtAbsCode)
    # concreteLine, isConcretized = concreteConverter.getConcreteLine(srcTokenizedCode, symbTable=symbTable,
    #                                                                 lineNo=editLineNo)