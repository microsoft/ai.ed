from copy import deepcopy
import pandas as pd

from Symbolic import DataStructs
from Symbolic.DataStructs import *


def parseGlobals(glob):
    globals_dict = {}
    for glb in glob.items():
        # print("{} -> {}".format(glb[0], type(glb[1])))
        typeStr = str(type(glb[1]))
        typeStr = typeStr.split('\'')[-2]
        globals_dict[glb[0]] = typeStr

    print(globals_dict)


def mergeIntDicts(dict1, dict2):
    dict_out = deepcopy(dict2)
    for key in dict1:
        if key in dict2:
            dict_out[key] += dict1[key]
        else:
            dict_out[key] = dict1[key]

    return dict_out


def joinList(li, joinStr='\n', func=str):
    return joinStr.join([func(i) for i in li])


def joinLL(lists, joinStrWord=' ', joinStrLine='\n', func=str, useConc=False):
    if useConc:
        listStrs = [joinConcrete(li, joinStrWord, func) for li in lists]
    else:
        listStrs = [joinList(li, joinStrWord, func) for li in lists]
    return joinList(listStrs, joinStrLine, func)

def joinConcrete(li, joinStr=' ', func=str):
    rstr = ""
    for ele in li:
        if ele == DataStructs.INDENT_SYMBOL * DataStructs.INDENT_SIZE:
            rstr += func(ele)
        else:
            rstr += func(ele) + " "
    if len(rstr) > 0 and rstr[-1] == " ":
        rstr = rstr[:-1]
    return rstr

def toInt(stri):
    if stri is None:
        return 0
    return int(stri)

def splitCode(source):
    srcList = source.splitlines()
    rval = []
    for line in srcList:
        rval.append(line.split(' '))
    return rval

def stringifyL(li):
    return [str(token) for token in li]


def stringifyLL(lists):
    return [stringifyL(li) for li in lists]


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def NoneAnd(bool1, bool2):
    '''Return and of 2 bools, provided no-one is none'''
    if bool1 is None and bool2 is None:
        return None
    if bool1 is None:
        return bool2
    if bool2 is None:
        return bool1

    return bool1 and bool2


def NoneOr(bool1, bool2):
    '''Return and of 2 bools, provided no-one is none'''
    if bool1 is None and bool2 is None:
        return None
    if bool1 is None:
        return bool2
    if bool2 is None:
        return bool1

    return bool1 or bool2


def splitCodeString(codeStr):
    '''
    Don't use this use str.splitlines() instead
    :param codeStr:
    :return:
    '''
    tmpSrcText = codeStr.split("\n")
    if tmpSrcText[0][-1] == '\r':  # find what line endings is used
        tmpSrcText = codeStr.split("\r\n")
    return tmpSrcText


def readSrcTrgtText(row):
    # sourceText = row['sourceText']
    # tmpSrcText = sourceText.split("\n")
    # if tmpSrcText[0][-1] == '\r':  # find what line endings is used
    #     sourceText = sourceText.split("\r\n")
    #     trgtText = row['targetText']
    #     trgtText = trgtText.split('\r\n')
    # else:
    #     sourceText = sourceText.split('\n')
    #     trgtText = row['targetText']
    #     trgtText = trgtText.split('\n')
    sourceText = str(row['sourceText']).splitlines()
    trgtText = str(row['targetText']).splitlines()
    return sourceText, trgtText


def convertEditDiffToDict(editDiff):
    rdict = dict()
    rdict['type'] = editDiff.editType
    rdict['start'] = editDiff.start
    rdict['end'] = editDiff.end
    rdict['insertString'] = editDiff.tokenStr
    return rdict

def convertFeedbacktoDict(feedback):
    rdict = dict()
    rdict['fullText'] = feedback.fullText
    rdict['msg1'] = feedback.msg1
    rdict['msg2'] = feedback.msg2
    rdict['actionMsg'] = feedback.actionMsg
    rdict['action'] = feedback.action
    rdict['tokens'] = feedback.tokens
    rdict['tokensText'] = feedback.tokensText
    rdict['misc'] = feedback.misc
    return rdict