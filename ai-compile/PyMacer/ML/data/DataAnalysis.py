from datetime import datetime

from sklearn.model_selection import train_test_split

from Symbolic.AbstractConverter import AbstractConverter
from Symbolic.CigarSrcTrgt import getUnicodeStrs, getUnicodeDicts
from Symbolic.DataStructs import Code
from Common.utils import *
import pandas as pd
import edlib
from timeit import default_timer as timer
from Common import ConfigFile as CF, utils


def getAlignDict(srcAbs, trgtAbs):
    dictAbs_Unicode, dictUnicode_Abs = getUnicodeDicts(srcAbs, trgtAbs)
    srcAbsUni = getUnicodeStrs(dictAbs_Unicode, srcAbs)
    trgtAbsUni = getUnicodeStrs(dictAbs_Unicode, trgtAbs)

    if len(trgtAbsUni) == 0:  # If the target Abs is empty (edlib crashes, hence handle separately)
        if len(srcAbsUni) == 0:  # And if the source Abs is empty as well
            cigar = ''  # Nothing to do
        else:
            cigar = str(len(srcAbsUni)) + 'D'  # Else, delete all source Abs
    else:
        cigar = edlib.align(trgtAbsUni, srcAbsUni, task='path')
    return cigar


def getStats(filename):
    df = pd.read_csv(filename)
    diffLen = []
    exceptions = []
    moreThanOne = 0
    srcAbstractionTime = 0
    trgtAbstractionTime = 0
    for i, row in df.iterrows():
        if i < 888:
            continue
        if i % 100 == 0:
            print('At {}/{}'.format(i, df.shape[0]))
        try:
            sourceText = row['sourceText']
            sourceText = sourceText.split("\n")
            trgtText = row['targetText']
            trgtText = trgtText.split('\n')

            start = timer()
            sourceCode = Code(sourceText)
            abstractConverter = AbstractConverter(sourceCode, inferTypes=False, debug=False)
            srcTokenizedCode, srcAbstractCode, srcSymbTable = abstractConverter.getAbstractionAntlr()
            srcAbstractionTime += timer() - start
            start = timer()
            trgtCode = Code(trgtText)
            abstractConverter = AbstractConverter(trgtCode, inferTypes=False, debug=False)
            trgtTokenizedCode, trgtAbstractCode, trgtSymbTable = abstractConverter.getAbstractionAntlr()
            trgtAbstractionTime += timer() - start
            if len(srcAbstractCode) != len(trgtAbstractCode):
                diffLen.append(i)
            differentLines = []
            for j in range(min(len(srcAbstractCode), len(trgtAbstractCode))):
                srcAbsLine = srcAbstractCode[j]
                trgtAbsLine = trgtAbstractCode[j]
                alignDict = getAlignDict(srcAbsLine, trgtAbsLine)
                if isinstance(alignDict, dict) and alignDict['editDistance'] > 0:
                    differentLines.append(j + 1)
            if len(differentLines) > 1:
                moreThanOne += 1
        except Exception as e:
            # traceback.print_stack()
            exceptions.append((i, str(e)))
            # break
    for ex in exceptions:
        print(ex)
    print('More than one line differs ', moreThanOne)
    print("Abstraction times: src :{} , trgt: {}".format(srcAbstractionTime, trgtAbstractionTime))


def splitMultiLineData(df):
    # df = pd.read_csv(filename)
    diffLen = []
    exceptions = []
    moreThanOne = 0
    srcAbstractionTime = 0
    trgtAbstractionTime = 0
    # outDf = df.copy()
    outDf = pd.DataFrame(columns=df.columns)
    outDf["sourceError"] = ""
    outDf["sourceLineTypeAbs"] = ""
    outDf["targetLineTypeAbs"] = ""
    moreThanOne = 0
    for i, row in df.iterrows():
        # if i < 64:
        #     continue

        if i % 100 == 0:
            print('At {}/{}'.format(i, df.shape[0]))
        try:
            sourceText, trgtText = utils.readSrcTrgtText(row)

            start = timer()
            sourceCode = Code(sourceText)
            abstractConverter = AbstractConverter(sourceCode, inferTypes=False, debug=False)
            srcTokenizedCode, srcAbstractCode, srcSymbTable = abstractConverter.getAbstractionAntlr()

            abstractConverter = AbstractConverter(sourceCode, inferTypes=True, debug=False)
            srcTypeTokenizedCode, srcTypeAbstractCode, srcTypeSymbTable = abstractConverter.getAbstractionAntlr()
            srcAbstractionTime += timer() - start

            start = timer()
            trgtCode = Code(trgtText)
            abstractConverter = AbstractConverter(trgtCode, inferTypes=False, debug=False)
            trgtTokenizedCode, trgtAbstractCode, trgtSymbTable = abstractConverter.getAbstractionAntlr()

            abstractConverter = AbstractConverter(trgtCode, inferTypes=True, debug=False)
            trgtTypeTokenizedCode, trgtTypeAbstractCode, trgtTypeSymbTable = abstractConverter.getAbstractionAntlr()
            trgtAbstractionTime += timer() - start

            if len(srcAbstractCode) != len(trgtAbstractCode):
                diffLen.append(i)
            differentLines = []

            for j in range(min(len(srcAbstractCode), len(trgtAbstractCode))):
                srcAbsLine = srcAbstractCode[j]
                trgtAbsLine = trgtAbstractCode[j]
                alignDict = getAlignDict(srcAbsLine, trgtAbsLine)
                # print('align', type(alignDict))
                if isinstance(alignDict, dict) and alignDict['editDistance'] > 0:
                    differentLines.append(j + 1)
                    tmpSrc = deepcopy(trgtText)
                    tmpSrcAbs = deepcopy(trgtAbstractCode)
                    tmpSrc[j] = sourceText[j]
                    tmpSrcAbs[j] = srcAbstractCode[j]
                    newRow = row.copy()
                    newRow['sourceText'] = joinList(tmpSrc)
                    newRow['targetText'] = row['targetText']
                    newRow['sourceAbs'] = joinLL(tmpSrcAbs)
                    newRow['targetAbs'] = joinLL(trgtAbstractCode)
                    newRow['sourceLineText'] = sourceText[j]
                    newRow['targetLineText'] = trgtText[j]
                    newRow['sourceLineAbs'] = joinList(srcAbstractCode[j], joinStr=' ')
                    newRow['targetLineAbs'] = joinList(trgtAbstractCode[j], joinStr=' ')
                    newRow['sourceLineTypeAbs'] = joinList(srcTypeAbstractCode[j], joinStr=' ')
                    newRow['targetLineTypeAbs'] = joinList(trgtTypeAbstractCode[j], joinStr=' ')
                    newRow['lineNums_Abs'] = str(j + 1)
                    tmpCode = Code(tmpSrc)
                    errInfo = tmpCode.getErrorInfo()
                    newRow['sourceError'] = str(errInfo)
                    if errInfo.lineNo != -1:
                        outDf = outDf.append(newRow)
                        # print(newRow)
                    del newRow
            if len(differentLines) > 1:
                moreThanOne += 1
        except Exception as e:
            print('exception ', str(e))
            exceptions.append((i, str(e)))
    for ex in exceptions:
        print(ex)
    print(len(exceptions))
    print(moreThanOne)
    print("Abstraction times: src :{} , trgt: {}".format(srcAbstractionTime, trgtAbstractionTime))
    print(outDf.shape)
    return outDf


def generateFullData(single=False):
    singleFile = './data/Python CEs/singleL_srcTrgtPairs.csv'
    multiFile = './data/Python CEs/multL_srcTrgtPairs.csv'
    zeroFile = './data/Python CEs/zeroDiff_srcTrgtPairs.csv'
    df = pd.read_csv(singleFile)
    outDf1 = splitMultiLineData(df)
    print("multi")
    df = pd.read_csv(multiFile)
    outDf2 = splitMultiLineData(df)
    print("zero")
    df = pd.read_csv(zeroFile)
    outDf3 = splitMultiLineData(df)
    if single:
        outDf = outDf1
    else:
        outDf = pd.concat([outDf1, outDf2, outDf3], ignore_index=True)

    outDf.to_csv(
        '/'.join(singleFile.split('/')[:-1]) + "/generatedSL" + str(datetime.now().strftime("%H_%M_%S")) + ".csv")


def createEmptyDF(df):
    outDf = pd.DataFrame(columns=df.columns)
    outDf["sourceError"] = ""
    outDf["sourceLineTypeAbs"] = ""
    outDf["targetLineTypeAbs"] = ""
    return outDf


def prepareAndAddRow(row, df, lineNos, sourceCode, sourceText, srcAbstractCode, srcTypeAbstractCode,
                     trgtText, trgtAbstractCode, trgtTypeAbstractCode):
    newRow = row.copy()
    if len(lineNos) == 0:
        lineNo = -1
    else:
        lineNo = int(lineNos[0])
    newRow['sourceAbs'] = joinLL(srcAbstractCode)
    newRow['targetAbs'] = joinLL(trgtAbstractCode)

    if lineNo > 0:
        newRow['sourceLineText'] = '' if lineNo > len(sourceText) else sourceText[
                                        lineNo - 1]  # since source/trgt might be missing a line
        newRow['targetLineText'] = '' if lineNo > len(trgtText) else trgtText[lineNo - 1]
        newRow['sourceLineAbs'] = '' if lineNo > len(srcAbstractCode) \
                                        else joinList(srcAbstractCode[lineNo - 1], joinStr=' ')
        newRow['targetLineAbs'] = '' if lineNo > len(trgtAbstractCode) \
                                        else joinList(trgtAbstractCode[lineNo - 1], joinStr=' ')
        newRow['sourceLineTypeAbs'] = '' if lineNo > len(srcTypeAbstractCode) \
                                        else joinList(srcTypeAbstractCode[lineNo - 1], joinStr=' ')
        newRow['targetLineTypeAbs'] = '' if lineNo > len(trgtTypeAbstractCode) \
                                        else joinList(trgtTypeAbstractCode[lineNo - 1], joinStr=' ')
    else:
        print("her", lineNo, end=" ")
        pass
    if len(lineNos) > 1:
        lineNos = list(map(str, lineNos))
        lineNos = str("\n".join(lineNos))
    elif len(lineNos) == 1:
        lineNos = lineNos[0]
    else:
        lineNos = -1
    newRow['lineNums_Abs'] = str(lineNos)

    errInfo = sourceCode.getErrorInfo()
    newRow['sourceError'] = str(errInfo)
    if errInfo.lineNo != -1:
        df = df.append(newRow)
    del newRow
    return df


def reorganizeData(new=False):
    if new:
        singleFile = '../../data/dataset-2/singleL.csv'
        multiFile = '../../data/dataset-2/multL.csv'
        zeroFile = '../../data/dataset-2/zeroL.csv'
    else:
        singleFile = '../../data/Python CEs/singleL_srcTrgtPairs.csv'
        multiFile = '../../data/Python CEs/multL_srcTrgtPairs.csv'
        zeroFile = '../../data/Python CEs/zeroDiff_srcTrgtPairs.csv'
    # zeroFile = './data/Python CEs/newZeroLine.csv'
    singleInput = pd.read_csv(singleFile)
    multiInput = pd.read_csv(multiFile)
    zeroInput = pd.read_csv(zeroFile)

    # singleOutput = pd.read_csv('./data/Python CEs/newSingleLine.csv')
    # multiOutput = pd.read_csv('./data/Python CEs/newMultiLine.csv')
    # zeroOutput = pd.read_csv('./data/Python CEs/newZeroLine.csv')
    singleOutput = createEmptyDF(singleInput)
    multiOutput = createEmptyDF(multiInput)
    zeroOutput = createEmptyDF(zeroInput)
    diffLen = []
    exceptions = []
    diffLen, excpetions, multiOutput, singleOutput, zeroOutput = \
        seperateDatasets(diffLen, exceptions, multiOutput, singleInput, singleOutput,
                                                        zeroOutput)

    diffLen, excpetions, multiOutput, singleOutput, zeroOutput = \
        seperateDatasets(diffLen, exceptions, multiOutput, multiInput, singleOutput,
                         zeroOutput)

    diffLen, excpetions, multiOutput, singleOutput, zeroOutput = \
        seperateDatasets(diffLen, exceptions, multiOutput, zeroInput, singleOutput,
                         zeroOutput)

    for ex in exceptions:
        print(ex)
    print(diffLen)
    singleOutput.to_csv('/'.join(singleFile.split('/')[:-1]) + "/newSingleLine.csv")
    multiOutput.to_csv('/'.join(multiFile.split('/')[:-1]) + "/newMultiLine.csv")
    zeroOutput.to_csv('/'.join(zeroFile.split('/')[:-1]) + "/newZeroLine.csv")


def seperateDatasets(diffLen, exceptions, multiOutput, singleInput, singleOutput, zeroOutput):
    for i, row in singleInput.iterrows():

        if i % 100 == 0:
            print('At {}/{}'.format(i, singleInput.shape[0]))
        try:
            sourceText, trgtText = utils.readSrcTrgtText(row)

            start = timer()
            sourceCode = Code(sourceText)
            abstractConverter = AbstractConverter(sourceCode, inferTypes=False, debug=False)
            srcTokenizedCode, srcAbstractCode, srcSymbTable = abstractConverter.getAbstractionAntlr()

            abstractConverter = AbstractConverter(sourceCode, inferTypes=True, debug=False)
            srcTypeTokenizedCode, srcTypeAbstractCode, srcTypeSymbTable = abstractConverter.getAbstractionAntlr()

            start = timer()
            trgtCode = Code(trgtText)
            abstractConverter = AbstractConverter(trgtCode, inferTypes=False, debug=False)
            trgtTokenizedCode, trgtAbstractCode, trgtSymbTable = abstractConverter.getAbstractionAntlr()

            abstractConverter = AbstractConverter(trgtCode, inferTypes=True, debug=False)
            trgtTypeTokenizedCode, trgtTypeAbstractCode, trgtTypeSymbTable = abstractConverter.getAbstractionAntlr()

            if len(srcAbstractCode) != len(trgtAbstractCode):
                diffLen.append(i)
            differentLines = []
            minLen = min(len(srcAbstractCode), len(trgtAbstractCode))
            for j in range(minLen):
                srcAbsLine = srcAbstractCode[j]
                trgtAbsLine = trgtAbstractCode[j]
                alignDict = getAlignDict(srcAbsLine, trgtAbsLine)
                # print('align', type(alignDict))
                if isinstance(alignDict, dict) and alignDict['editDistance'] > 0:
                    differentLines.append(j + 1)
                elif (len(srcAbsLine) == 0 and len(trgtAbsLine) != 0) or (len(srcAbsLine) != 0 and len(trgtAbsLine) == 0):
                    differentLines.append(j + 1)

            for j in range(abs(len(srcAbstractCode) - len(trgtAbstractCode))):
                l = minLen + j
                differentLines.append(l + 1)

            if len(differentLines) == 0:
                # zeroDiff
                zeroOutput = prepareAndAddRow(row, zeroOutput, differentLines, sourceCode, sourceText,
                                              srcAbstractCode,
                                              srcTypeAbstractCode, trgtText, trgtAbstractCode, trgtTypeAbstractCode)

            elif len(differentLines) == 1:
                # singleDiff
                singleOutput = prepareAndAddRow(row, singleOutput, differentLines, sourceCode, sourceText,
                                                srcAbstractCode,
                                                srcTypeAbstractCode, trgtText, trgtAbstractCode, trgtTypeAbstractCode)

            else:

                multiOutput = prepareAndAddRow(row, multiOutput, differentLines, sourceCode, sourceText,
                                               srcAbstractCode,
                                               srcTypeAbstractCode, trgtText, trgtAbstractCode, trgtTypeAbstractCode)

        except Exception as e:
            print('exception ', str(e))
            exceptions.append((i, str(e)))
    return diffLen, exceptions, multiOutput, singleOutput, zeroOutput


def splitData(filename):
    df = pd.read_csv(filename)
    train, test = train_test_split(df, test_size=0.2, random_state=42, shuffle=True)
    train.to_csv("/".join(filename.split('/')[:-1]) + "/train" + filename.split("/")[-1])
    test.to_csv("/".join(filename.split('/')[:-1]) + "/test" + filename.split("/")[-1])


def mergeCSVs(csv1, csv2, out_file):
    df1 = pd.read_csv(csv1)
    df2 = pd.read_csv(csv2)

    frames = [df1, df2]
    outDf = pd.concat(frames)
    outDf.to_csv(out_file, index=False)

if __name__ == '__main__':
    # getStats(filename='./data/Python CEs/zeroDiff_srcTrgtPairs.csv')
    # splitMultiLineData(filename='./data/Python CEs/singleL_srcTrgtPairs.csv')
    # generateFullData()
    # splitData(CF.dataPath + '/newSingleLine.csv')
    # reorganizeData(new=True)
    mergeCSVs(CF.dataPath + "/newSingleLine.csv", CF.newDataPath + "/newSingleLine.csv", CF.dataPath + "/mergedNewSingleLine.csv")
    # mergeCSVs(CF.fnameSingleL_Test_new, CF.fnameSingleL_Test, CF.dataPath + "/mergedTest.csv")
