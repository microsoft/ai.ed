import os
from Symbolic.DataStructs import *
import pandas as pd
from Common import ConfigFile as CF, utils

def saveAllErrs(allErrs):
    data = []
    for msg in allErrs:
        iden = allErrs[msg]
        data.append((iden, msg))

    df = pd.DataFrame(data=data, columns=['id', 'errorText'])
    df.to_csv(CF.fname_newErrIDs, index=False)

def getAllErrs(fname):
    allErrs = dict()
    if not os.path.exists(fname):
        generateErrSet(fname)

    df = pd.read_csv(fname, index_col=False)
    for i, row in df.iterrows():
        allErrs[row['errorText']] = row['id']

    return allErrs


def getErrIDs(allErrs, codeObj, lineNum=None):
    eids = []

    errInfo = codeObj.getErrorInfo()
    errorAbs = errInfo.getAbs()
    if errorAbs not in allErrs:
        allErrs[errorAbs] = len(allErrs) + 1
        saveAllErrs(allErrs)
    eids.append(allErrs[errorAbs])

    return sorted(eids)


def getErrSet(allErrs, codeObj, lineNum=None):
    eids = getErrIDs(allErrs, codeObj, lineNum)
    return set(eids)


def getErrSetStr(allErrs, codeObj, lineNum=None):
    errSet = getErrSet(allErrs, codeObj, lineNum)
    return utils.joinList(errSet, ';') + ';'


def populateErrIds(filename):
    # filename = CF.fnameSingleL_Train
    df = pd.read_csv(filename)

    allErrs = getAllErrs(CF.fname_newErrIDs)
    classes, classesRepeat, newErrSets = [], [], []
    mult = 10

    for i, row in df.iterrows():
        # oldClass = row['errSet_diffs']
        sourceText, trgtText = utils.readSrcTrgtText(row)
        codeObj = Code(sourceText)

        newErrsetStr = getErrSetStr(allErrs, codeObj)

        newErrSets.append(newErrsetStr)

        if i >= len(df) * mult / 100:
            print(str(mult) + '%', end=' ', flush=True)
            mult += 10

    df['newErrSet'] = newErrSets
    df.to_csv(filename, index=False)


def disp_props(filename):
    # global errSet, n
    df = pd.read_csv(filename)
    srcLines = df['sourceText']
    errSet = set()
    blanks = []
    errorFree = []
    for id, srcLine in enumerate(srcLines):
        if isinstance(srcLine, str):
            srcLine = srcLine.split("\n")
            srcObj = Code(srcLine)
            errInfo = srcObj.getErrorInfo()
            if errInfo.errClass == "No Error":
                errorFree.append(id)
            else:
                errSet.add(errInfo.getAbs())
        else:
            blanks.append(id)
    errSet = list(errSet)
    n = len(errSet)
    print("# unique errors: {}, blanks: {}, no errors: {}".format(n, len(blanks), len(errorFree)))
    return errSet


def generateErrSet(fname):
    filename_single = "../data/Python CEs/singleL_srcTrgtPairs.csv"
    filename_single = os.path.abspath(filename_single)
    filename_multi = "../data/Python CEs/multL_srcTrgtPairs.csv"
    filename_multi = os.path.abspath(filename_multi)
    filename_zero = "../data/Python CEs/zeroDiff_srcTrgtPairs.csv"
    filename_zero = os.path.abspath(filename_zero)
    errSet_Final = []
    errSet_Final.extend(disp_props(filename_zero))
    errSet_Final.extend(disp_props(filename_single))
    errSet_Final.extend(disp_props(filename_multi))
    errSet_Final = list(set(errSet_Final))
    print(len(errSet_Final))
    error_dict = dict()
    for i, bl in enumerate(errSet_Final):
        error_dict[i + 1] = bl

    errSet = pd.DataFrame(error_dict.items(), columns=['id', 'errorText'])
    errSetPath = CF.dataPath + "/" + fname
    errSet.to_csv(errSetPath, index=False)

if __name__ == '__main__':
    pass
    populateErrIds(CF.fnameSingleL_Train_merged)
    print()
    populateErrIds(CF.fnameSingleL_Test_merged)
    # generateErrSet("errSet.csv")