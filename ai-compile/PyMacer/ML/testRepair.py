import sys, os
from datetime import datetime
from difflib import SequenceMatcher
from statistics import mean
sys_path = os.path.abspath(".\\")
print(sys_path)
sys.path.insert(1, sys_path)
from ML.data.DataAnalysis import getAlignDict
from ML.rcAnalysis import getFeedbackFromRepairClass, getLineDiff


def error_args():
    print("Usage: python testRepair.py <dataset/path-to-test-file> <PredK>")
    sys.exit(1)


# if len(sys.argv) != 3:
#     error_args()

from Symbolic.DataStructs import *
from Symbolic import ClusterError, IndentationParser, AbstractHelper
from Common import ConfigFile as CF, utils
from Symbolic import AbstractConverter, ConcreteConverter
from ML import Predict, Globals
# from srcT.Prediction import PredictWithNewColLoc
import pandas as pd, copy
from timeit import default_timer as timer
from ML.Globals import repl_encoder, rest_encoder, del_encoder, ins_encoder, dir_name, \
    opt, flags, new_data, merged, new_encoder

wo_err_id = opt & flags['weid']
more_data = opt & flags['md']
inferTypes = opt & flags['ti']

slash = os.sep
outdir_name = os.path.split(Globals.dir_name)[1]
outdir_path = CF.pathOut + slash + outdir_name

if not os.path.exists(outdir_path):
    os.makedirs(outdir_path)

errInfo_filePath = outdir_path + slash + "error_stats"
resultsPred_filePath = outdir_path + slash + 'results_PredAt'

print("Results path: ", resultsPred_filePath)

# region: Global edits
use_compiler_msg = False
ignore_warning = True
# use_new_col_loc = True
debug = False
activeLocalization = True
useTracers_errLoc = True  # Use tracer's loc? Line-1, Line, Line+1
flagErrSet_Line = False  # Pass only line specific err-sets to Macer?
is_multi = False
AllErrs = ClusterError.getAllErrs(CF.fname_newErrIDs)


# endregion

# region: Accuracy

def checkRelevant(predText, predErrAbsLines, trgtText, trgtErrAbsLines):
    trgtLL = [line.split() for line in trgtErrAbsLines.splitlines()]
    predLL = []
    for line in predErrAbsLines:
        if line != []:
            predLL.append(line)
    isRelevant = trgtLL == predLL

    if isRelevant == False:
        tgt_text = [line.split() for line in trgtText.splitlines()]
        pred_text = [line.split() for line in predText.splitlines()]
        if tgt_text == pred_text:
            isRelevant = True

    return isRelevant


def checkRelevant2(predAbsLine, trgtAbsLine):
    return predAbsLine == trgtAbsLine


def calcAccuracy(actLinesStr, predLineNums, trgtText, trgtErrAbsLines, predErrAbsLines, predErrLines, predText):
    # isLocated
    isLocated = True

    try:
        for actLineNum in actLinesStr.splitlines():
            if int(actLineNum) not in predLineNums:
                isLocated = False
    except ValueError as e:
        isLocated = False

    # isRelevant
    isRelevant = checkRelevant(predText, predErrAbsLines, trgtText, trgtErrAbsLines)

    # isCompiled
    predCodeObj = Code(predText)
    isCompiled = predCodeObj.getErrorInfo().lineNo == -1

    return isLocated, isRelevant, isCompiled


# endregion

# region: 3-Phase
def errLoc(activeLocalization, srcCodeObj, actLinesStr, useTracers_errLoc=False):
    '''If errorLocalization is active, return compiler reported line.
Else, return the ideal (source-target text diff) lines'''
    if activeLocalization:
        predLines = [srcCodeObj.getErrorInfo().lineNo]

        if useTracers_errLoc:
            prevLines = [line - 1 for line in predLines]
            nextLines = [line + 1 for line in predLines]
            return predLines + prevLines + nextLines

        return predLines

    return actLinesStr.split('\n')


def getErrLineNumbers(srcCodeObj, srcLines, actLinesStr):
    lineNums = errLoc(activeLocalization, srcCodeObj, actLinesStr, useTracers_errLoc)

    ###################[ Using Compiler Message ]##################

    extra_lines = 0
    if use_compiler_msg:

        errInfo = srcCodeObj.getErrorInfo()

        ids = set(errInfo.findIDs())

        for x, line in enumerate(srcLines):
            # concLine, isConc = ConcreteWrapper.attemptConcretization(srcCodeObj, x + 1, srcAbsLines[x])
            # if isConc:
            for tok in line:
                if tok in ids and tok != ';' and tok != ',' and (not ((x + 1) in lineNums)):
                    lineNums.append(x + 1)
                    extra_lines += 1

    return lineNums, extra_lines

def repairErrLine(srcCodeObj, srcTokenizedCode, symbTable, repairLines, repairAbsLines, srcAbsLine, trgtLine,
                  trgtAbsLine, errSetLine, lineNum,
                  predErrAbsLines, predErrLines, predAtK, err_msg, trgtErrAbsLines, gold_repair_classes):
    '''Pred@K and concretize the best line (with least errors)'''
    isConcretized, isExactMatch = None, None
    bestPredAbsLine, bestPredLine = None, None
    bestPredAbsLines, bestPredLines = repairAbsLines, repairLines

    prePredCodeObj = Code(utils.joinList(repairLines))
    # minNumErrs = prePredCodeObj.getNumErrors()
    errInfo = prePredCodeObj.getErrorInfo()

    corr_pred_rep = None
    bestRepairClass = None
    # if use_new_col_loc:
    tmpPredAbsLines, corr_pred_rep, repair_classes = \
        Predict.predictAbs(srcAbsLine, errSetLine, trgtAbsLine, predAtK, err_msg, gold_repair_classes)
    # else:
    #     tmpPredAbsLines, corr_pred_rep = \
    #         Predictv2.predictAbs(srcAbsLine, errSetLine, trgtAbsLine, predAtK, err_msg, gold_repair_classes)
    for x, predAbsLine in enumerate(tmpPredAbsLines):
        # Create copy of previous obtained repairLines, and replace with predictedLines
        predLines, predAbsLines = copy.deepcopy(repairLines), copy.deepcopy(repairAbsLines)
        predAbsLines[lineNum - 1] = utils.joinList(predAbsLine, joinStr=' ')

        # Concretize the predicted abstract fix

        start_concrete = timer()
        predLine, tempIsConcretized = ConcreteConverter.attemptConcretization(srcCodeObj, srcTokenizedCode, symbTable, predAbsLine, lineNum,
                                                                              debug, inferTypes)
        Globals.concretization += timer() - start_concrete
        predLines[lineNum - 1] = utils.joinConcrete(predLine, joinStr=' ')

        # Concretization success?
        isConcretized = utils.NoneAnd(isConcretized, tempIsConcretized)
        # tempIsExactMatch = checkRelevant2(predAbsLine, trgtAbsLine)
        tempIsExactMatch = checkRelevant2(predAbsLine, trgtErrAbsLines.split(' '))
        isExactMatch = utils.NoneOr(isExactMatch, tempIsExactMatch)

        # Find best prediction
        predCodeObj = Code(utils.joinList(predLines))
        currErrInfo = predCodeObj.getErrorInfo()
        # if minNumErrs is None or predCodeObj.getNumErrors() < minNumErrs:
        if errInfo.lineNo != -1 and (currErrInfo.lineNo == -1 or currErrInfo.lineNo > errInfo.lineNo):
            '''
                Assuming an error to be resolved if either the program gets compiled (lineNo = -1) or pick the repair
                for which the new Error line number is farthest from the current Error Line number.
            '''
            # TODO: Might be better ways to handle this
            # minNumErrs = predCodeObj.getNumErrors()
            errInfo = currErrInfo
            bestPredAbsLines, bestPredLines = predAbsLines, predLines
            bestPredAbsLine, bestPredLine = predAbsLine, predLine
            bestRepairClass = repair_classes[x]
            # if is_multi:
            #     repairAbsLines = bestPredAbsLines
            #     repairLines = bestPredLines

    return bestPredAbsLine, bestPredLine, bestPredAbsLines, bestPredLines, \
           isConcretized, isExactMatch, corr_pred_rep, bestRepairClass


def runPerLine(srcCodeObj, srcTokenizedCode, symbTable, srcLines, trgtLines, srcAbsLines, trgtAbsLines, errSet, lineNums, predAtK, err_msg,
               trgtErrAbsLines, actLineList, gold_repair_classes):
    '''For each compiler error line, call predErrLine'''
    srcErrLines, srcErrAbsLines = [], []
    predErrLines, predErrAbsLines = [], []
    repairLines, repairAbsLines = copy.deepcopy(srcLines), copy.deepcopy(srcAbsLines)
    isConcretized, isExactMatch = None, None
    errLinesDict = {}
    corr_pred_rep_final = False
    predLineNums = []
    bestRepairClass = []
    # For each compiler flagged lineNums
    for lineNum in lineNums:
        lineNum = int(lineNum)

        if lineNum <= min([len(srcLines), len(srcAbsLines)]):  # If compiler returned valid line-num
            srcLine, srcAbsLine = srcLines[lineNum - 1], srcAbsLines[
                lineNum - 1]  # lineNum-1 since off-by-one
            trgtLine, trgtAbsLine = None, None
            if lineNum <= min([len(trgtLines), len(trgtAbsLines)]) and lineNum > 0:
                trgtLine, trgtAbsLine = trgtLines[lineNum - 1], trgtAbsLines[lineNum - 1]
            srcErrLines.append(srcLine), srcErrAbsLines.append(srcAbsLine)

            # Use ErrSet at line=lineNum? Or at program-level
            errSetLine = errSet
            if flagErrSet_Line:
                errSetLine = ClusterError.getErrSetStr(AllErrs, srcCodeObj, lineNum=lineNum)

            # Predict@K the concrete repair line
            predAbsLine, predLine, repairAbsLines, repairLines, \
            tempIsConcretized, tempIsExactMatch, corr_pred_rep, bestRepairClass_tmp = \
                repairErrLine(srcCodeObj, srcTokenizedCode, symbTable, \
                              repairLines, repairAbsLines, srcAbsLine, trgtLine, trgtAbsLine, errSetLine, lineNum, \
                              predErrAbsLines, predErrLines, predAtK, err_msg, trgtErrAbsLines, gold_repair_classes)

            # Concretization success?
            isConcretized = utils.NoneAnd(isConcretized, tempIsConcretized)
            if lineNum in actLineList:
                corr_pred_rep_final = utils.NoneOr(corr_pred_rep_final, corr_pred_rep)
            # isExactMatch = H.NoneOr(isExactMatch, tempIsExactMatch)
            if lineNum in actLineList and tempIsExactMatch:
                isExactMatch = True
            # Record the predicted abstract and concrete line
            if predAbsLine is not None:
                predErrAbsLines.append(predAbsLine)
                predErrLines.append(predLine)
                predLineNums.append(lineNum)
                bestRepairClass.append(bestRepairClass_tmp)
                if tempIsConcretized:
                    errLinesDict[lineNum] = predLine

    predText = utils.joinList(repairLines)

    return predText, srcErrLines, predErrLines, srcErrAbsLines, predErrAbsLines, isConcretized, \
           isExactMatch, corr_pred_rep_final, bestRepairClass, predLineNums


# endregion

def fixOnce(srcText, srcCodeObj, trgtLines, trgtErrAbsLines, trgtAbsLines,
            initErrInfo, actLinesStr, predAtK):
    # initErrInfo = initErrInfo
    indentFixed = False
    indentError = False
    repair_class_dict = {}
    if IndentationParser.checkIndentationError(initErrInfo):
        start_indent = timer()
        tmpCode, fixed = IndentationParser.fixIndentation(srcCodeObj, initErrInfo)
        Globals.indent += timer() - start_indent
        indentError = True
        if fixed:
            # might not mean all errors are fixed just the indentation errors are fixed
            srcCodeObj = deepcopy(tmpCode)
            indentFixed = True
            repair_class_dict[initErrInfo.lineNo] = repair_class_dict.get(initErrInfo.lineNo, [])
            repair_class_dict[initErrInfo.lineNo].append(-1)

    initErrInfo = srcCodeObj.getErrorInfo()
    errInfo = deepcopy(initErrInfo)
    isCompiled = True
    isMoved = True
    predText = utils.joinList(srcCodeObj.source, joinStr="\n")
    predErrLines = []
    predErrAbsLines = []
    isConcretized = True
    isExactMatch = False
    corr_pred_rep_final = False
    lineNums = []
    predErrLines = []
    srcErrLines = []
    srcErrAbsLines = []
    gold_repair_classes = []

    if initErrInfo.lineNo != -1:  # If there are errors

        start = timer()
        abstractConverter = AbstractConverter.AbstractConverter(srcCodeObj, inferTypes=inferTypes, debug=debug)
        srcTokenizedCode, srcAbsLines, srcSymbTable = abstractConverter.getAbstractionAntlr()
        # srcLines = utils.joinLL(AbstractHelper.getPlainCodeFromTokenizedCode(srcTokenizedCode)).splitlines()
        srcLines = srcCodeObj.source
        Globals.abstraction += timer() - start

        errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)

        lineNums, extra_lines = getErrLineNumbers(srcCodeObj, srcLines, actLinesStr)

        ############################################################################
        for actLine in actLinesStr.splitlines():
            if actLine == 'nan':
                actLine = len(srcAbsLines) + 1
            else:
                actLine = int(actLine)
            if actLine > len(srcAbsLines):
                continue
            x = [] if actLine > len(srcAbsLines) else srcAbsLines[actLine - 1]
            # y = trgtErrAbsLines.split(' ')
            y = [] if actLine > len(trgtAbsLines) else trgtAbsLines[actLine - 1]
            sm = SequenceMatcher(None, x, y)
            repl_str = []
            del_str = []
            ins_str = []
            for opcodes in sm.get_opcodes():
                if opcodes[0] == 'equal':
                    continue
                elif opcodes[0] == 'replace':
                    tmp_str = ''
                    for st in x[opcodes[1]:opcodes[2]]:
                        tmp_str += '- ' + st + '\n'
                    for st in y[opcodes[3]:opcodes[4]]:
                        tmp_str += '+ ' + st + '\n'
                    repl_str.append(tmp_str[:-1])
                elif opcodes[0] == 'insert':
                    tmp_str = ''
                    for st in y[opcodes[3]:opcodes[4]]:
                        tmp_str += '+ ' + st + '\n'
                    ins_str.append(tmp_str[:-1])
                elif opcodes[0] == 'delete':
                    tmp_str = ''
                    for st in x[opcodes[1]:opcodes[2]]:
                        tmp_str += '- ' + st + '\n'
                    del_str.append(tmp_str[:-1])
            tmp_str = ''

            # if replace[i]!=[] and insert[i]==[] and delete[i]==[]:
            #     tmp_str += 'rep\n'
            # elif replace[i]==[] and insert[i]!=[] and delete[i]==[]:
            #     tmp_str += 'ins\n'
            # elif replace[i]==[] and insert[i]==[] and delete[i]!=[]:
            #     tmp_str += 'del\n'
            # else:
            #     tmp_str += 'res\n'
            if not wo_err_id:
                tmp_str += errSet + '\n'
            for repl in repl_str:
                tmp_str += repl + '\n'
            for dlt in del_str:
                tmp_str += dlt + '\n'
            for ins in ins_str:
                tmp_str += ins + '\n'
            gold_repair_classes.append(tmp_str[:-1])
        #############################################################################

        # Run prediction on all erroneous lines
        actLineList = [int(l) for l in actLinesStr.splitlines()]
        lineNums = sorted(list(set(lineNums)))
        # actLineList = []
        predText, srcErrLines, predErrLines, srcErrAbsLines, predErrAbsLines, \
        isConcretized, isExactMatch, corr_pred_rep_final, bestRepairClass, lineNo = \
            runPerLine(srcCodeObj, srcTokenizedCode, srcSymbTable, srcLines, trgtLines, srcAbsLines, trgtAbsLines, errSet, lineNums,
                       predAtK, errInfo, trgtErrAbsLines, actLineList, gold_repair_classes)

        for bc, l in zip(bestRepairClass, lineNo):
            repair_class_dict[l] = repair_class_dict.get(l, [])
            repair_class_dict[l].append(bc)
        predCodeObj = Code(predText)
        predErrInfo = predCodeObj.getErrorInfo()
        isCompiled = predErrInfo.lineNo == -1
        isMoved = initErrInfo.lineNo < predErrInfo.lineNo

    return predText, predErrLines, predErrAbsLines, indentError, indentFixed, isCompiled, isMoved, \
           isConcretized, isExactMatch, corr_pred_rep_final, \
           predErrLines, lineNums, srcErrLines, srcErrAbsLines, gold_repair_classes, repair_class_dict

def fixIncrementally(srcText, trgtText, srcID, trgtID, trgtErrAbsLines, actLinesStr, predAtK):
    srcCodeObj, trgtCodeObj = Code(srcText, codeID=srcID), Code(trgtText, codeID=trgtID)
    srcLines, trgtLines = srcText.splitlines(), trgtText.splitlines()
    errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)

    start = timer()
    abstractConverter = AbstractConverter.AbstractConverter(trgtCodeObj, inferTypes=inferTypes, debug=debug)
    trgtTokenizedCode, trgtAbsLines, trgtSymbTable = abstractConverter.getAbstractionAntlr()
    Globals.abstraction += timer() - start

    repairText = deepcopy(srcText)
    repairLines = repairText.splitlines()
    repCodeObj = Code(repairLines)
    fixed = False
    i = 0
    fin_indentError = False
    fin_indentFixed = False
    fin_ExactMatch = False
    fin_Concretized = False
    fin_corr_pred_rep = False
    fin_predErrLines = []
    fin_lineNums = []
    fin_srcErrLines = []
    fin_srcErrAbsLines = []
    fin_gold_repair_classes = []
    repair_class_dict = {}
    while not fixed and i < 5:

        errInfo = repCodeObj.getErrorInfo()
        predText, predErrLines, predErrAbsLines, indentError, indentFixed, isCompiled, isMoved, \
                isConcretized, isExactMatch, corr_pred_rep_final, \
        predErrLines, lineNums, srcErrLines, srcErrAbsLines, gold_repair_classes, bestRepairClass = \
            fixOnce(repairText, repCodeObj, trgtLines, trgtErrAbsLines, trgtAbsLines,
            errInfo, actLinesStr, predAtK)
        fin_indentError = utils.NoneOr(fin_indentError, indentError)
        fin_indentFixed = utils.NoneOr(fin_indentFixed, indentFixed)
        fin_ExactMatch = utils.NoneAnd(fin_ExactMatch, isExactMatch)
        fin_Concretized = utils.NoneAnd(fin_Concretized, isConcretized)
        fin_predErrLines.extend(predErrLines)
        fin_lineNums.extend(lineNums)
        fin_srcErrLines.extend(srcErrLines)
        fin_srcErrAbsLines.extend(srcErrAbsLines)
        fin_gold_repair_classes.extend(gold_repair_classes)
        fin_corr_pred_rep = utils.NoneOr(fin_corr_pred_rep, corr_pred_rep_final)
        # repair_classes.append(bestRepairClass)

        for k, v in bestRepairClass.items():
            repair_class_dict[k] = repair_class_dict.get(k, [])
            repair_class_dict[k].extend(v)
        if isCompiled:
            fixed = True
            repairText = predText
            repairLines = repairText.splitlines()
            repCodeObj = Code(repairLines)
        if isMoved:
            repairText = predText
            repairLines = repairText.splitlines()
            repCodeObj = Code(repairLines)
        if not isCompiled and not isMoved:
            break
        i+= 1

    return isCompiled, repairText, repairLines, fin_Concretized, fin_indentFixed, fin_indentError, \
           fin_ExactMatch, fin_corr_pred_rep, fin_predErrLines, fin_lineNums, fin_srcErrLines, \
           fin_srcErrAbsLines, errSet, fin_gold_repair_classes, repair_class_dict
# region: Main functions

def run(df, predAtK):
    startTime = timer()
    columns = ['id', 'sourceText', 'targetText', 'predText', 'actLineNums', 'predLineNums', \
               'actSourceLine', 'localSourceLine', 'targetLine', 'predLine', \
               'actSourceAbsLine', 'localSourceAbsLine', 'targetAbsLine', \
               'errSet', 'isConcretized', 'isExactMatch', 'isCompiled']
    results = []  # True to turn on localization Module, False to turn off
    # allErrors = ClusterError.getAllErrs()

    ##################################################################
    repair_class_freq_dict = {}
    repair_class_repair_dict = {}
    repair_class_exact_dict = {}
    repair_class_type_dict = {}
    err_class_dict = {}
    zero_shot = 0
    zero_shot_compiled = 0
    zero_shot_exact = 0
    repair_class_pred = 0
    more_than_one_line = 0

    repl_classes = list(repl_encoder.classes_)
    ins_classes = list(ins_encoder.classes_)
    del_classes = list(del_encoder.classes_)
    rest_classes = list(rest_encoder.classes_)

    iter_list = sorted(repl_classes + ins_classes + del_classes + rest_classes)

    repl_classes = set(list(repl_encoder.classes_))
    ins_classes = set(list(ins_encoder.classes_))
    del_classes = set(list(del_encoder.classes_))
    rest_classes = set(list(rest_encoder.classes_))

    # iter_list = sorted(list(set(list(repl_encoder.classes_) + list(ins_encoder.classes_) + list(del_encoder.classes_)\
    # + list(rest_encoder.classes_))))

    for cls in iter_list:
        repair_class_freq_dict[cls] = 0
        repair_class_exact_dict[cls] = 0
        repair_class_repair_dict[cls] = 0
        # if cls in repl_encoder.classes_:
        #     repair_class_type_dict[cls] = 'repl'
        # elif cls in ins_encoder.classes_:
        #     repair_class_type_dict[cls] = 'ins'
        # elif cls in del_encoder.classes_:
        #     repair_class_type_dict[cls] = 'del'
        # elif cls in rest_encoder.classes_:
        #     repair_class_type_dict[cls] = 'rest'
        if cls in repl_classes:
            repair_class_type_dict[cls] = 'repl'
        elif cls in ins_classes:
            repair_class_type_dict[cls] = 'ins'
        elif cls in del_classes:
            repair_class_type_dict[cls] = 'del'
        elif cls in rest_classes:
            repair_class_type_dict[cls] = 'rest'
    ##################################################################

    err_lines_ratio = []
    tot_extra_err_lines = 0
    indentationErrorsFixed = 0
    totalIndentationErrs = 0
    not_compiled = 0

    ############[ ERROR STATS ]##############
    errInfo_dict = {}
    #########################################
    # For each erroneous code
    for i, row in df.iterrows():
        srcID, trgtID = str(row['id']) + '_source', str(row['id']) + '_target'
        srcText, trgtText = str(row['sourceText']), str(row['targetText'])
        trgtErrLines = str(row['targetLineText']).strip()
        if inferTypes:
            trgtErrAbsLines = str(row['targetLineTypeAbs']).strip()
        else:
            trgtErrAbsLines = str(row['targetLineAbs']).strip()
        actLinesStr = str(row['lineNums_Abs'])

        # Parse the source/erroneous code
        # srcCodeObj, trgtCodeObj = Code(srcText, codeID=srcID), Code(trgtText, codeID=trgtID)
        # srcLines, trgtLines = srcText.splitlines(), trgtText.splitlines()

        # Fetch its abstraction
        # srcAbsLines = AbstractWrapper.getProgAbstraction(srcCodeObj)
        # trgtAbsLines = AbstractWrapper.getProgAbstraction(trgtCodeObj)

        # sourceCode = Code(srcText)
        # initErrInfo = srcCodeObj.getErrorInfo()
        # indentFixed = False
        # if IndentationParser.checkIndentationError(initErrInfo):
        #     tmpCode, fixed = IndentationParser.fixIndentation(srcCodeObj, initErrInfo)
        #     totalIndentationErrs += 1
        #     if fixed:
        #         # might not mean all errors are fixed just the indentation errors are fixed
        #         srcCodeObj = deepcopy(tmpCode)
        #         indentFixed = True
        # abstractConverter = AbstractConverter.AbstractConverter(srcCodeObj, inferTypes=inferTypes, debug=debug)
        # srcTokenizedCode, srcAbsLines, srcSymbTable = abstractConverter.getAbstractionAntlr()
        # errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)

        # trgtCode = Code(trgtText)
        # abstractConverter = AbstractConverter.AbstractConverter(trgtCodeObj, inferTypes=inferTypes, debug=debug)
        # trgtTokenizedCode, trgtAbsLines, trgtSymbTable = abstractConverter.getAbstractionAntlr()

        # Fetch Line numbers
        # lineNums = errLoc(activeLocalization, srcCodeObj, actLinesStr, useTracers_errLoc)

        ###################[ Using Compiler Message ]##################

        # if use_compiler_msg:
        #     extra_lines = 0
        #
        #     errInfo = srcCodeObj.getErrorInfo()
        #
        #     ids = set(errInfo.findIDs())
        #
        #     for x, line in enumerate(srcLines):
        #         # concLine, isConc = ConcreteWrapper.attemptConcretization(srcCodeObj, x + 1, srcAbsLines[x])
        #         # if isConc:
        #         for tok in line:
        #             if tok in ids and tok != ';' and tok != ',' and (not ((x + 1) in lineNums)):
        #                 lineNums.append(x + 1)
        #                 extra_lines += 1
        #
        #     tot_extra_err_lines += extra_lines
        #     err_lines_ratio.append(len(lineNums) / len(srcAbsLines))
        ###########################################################################

        ############################################################################
        # gold_repair_classes = []
        # for actLine in actLinesStr.splitlines():
        #     if actLine == 'nan':
        #         actLine = len(srcAbsLines) + 1
        #     else:
        #         actLine = int(actLine)
        #     if actLine > len(srcAbsLines):
        #         continue
        #     x = [] if actLine > len(srcAbsLines) else srcAbsLines[actLine - 1]
        #     # y = trgtErrAbsLines.split(' ')
        #     y = [] if actLine > len(trgtAbsLines) else trgtAbsLines[actLine - 1]
        #     sm = SequenceMatcher(None, x, y)
        #     repl_str = []
        #     del_str = []
        #     ins_str = []
        #     for opcodes in sm.get_opcodes():
        #         if opcodes[0] == 'equal':
        #             continue
        #         elif opcodes[0] == 'replace':
        #             tmp_str = ''
        #             for st in x[opcodes[1]:opcodes[2]]:
        #                 tmp_str += '- ' + st + '\n'
        #             for st in y[opcodes[3]:opcodes[4]]:
        #                 tmp_str += '+ ' + st + '\n'
        #             repl_str.append(tmp_str[:-1])
        #         elif opcodes[0] == 'insert':
        #             tmp_str = ''
        #             for st in y[opcodes[3]:opcodes[4]]:
        #                 tmp_str += '+ ' + st + '\n'
        #             ins_str.append(tmp_str[:-1])
        #         elif opcodes[0] == 'delete':
        #             tmp_str = ''
        #             for st in x[opcodes[1]:opcodes[2]]:
        #                 tmp_str += '- ' + st + '\n'
        #             del_str.append(tmp_str[:-1])
        #     tmp_str = ''
        #
        #     # if replace[i]!=[] and insert[i]==[] and delete[i]==[]:
        #     #     tmp_str += 'rep\n'
        #     # elif replace[i]==[] and insert[i]!=[] and delete[i]==[]:
        #     #     tmp_str += 'ins\n'
        #     # elif replace[i]==[] and insert[i]==[] and delete[i]!=[]:
        #     #     tmp_str += 'del\n'
        #     # else:
        #     #     tmp_str += 'res\n'
        #     if not wo_err_id:
        #         tmp_str += errSet + '\n'
        #     for repl in repl_str:
        #         tmp_str += repl + '\n'
        #     for dlt in del_str:
        #         tmp_str += dlt + '\n'
        #     for ins in ins_str:
        #         tmp_str += ins + '\n'
        #     gold_repair_classes.append(tmp_str[:-1])
        #############################################################################

        # errInfo = srcCodeObj.getErrorInfo()

        # if errInfo.lineNo != -1:  # If there are errors
        #
        #     # Run prediction on all erroneous lines
        #     actLineList = [int(l) for l in actLinesStr.splitlines()]
        #     lineNums = sorted(list(set(lineNums)))
        #     # actLineList = []
        #     if len(actLineList) > 1:
        #         more_than_one_line += 1
        #     predText, srcErrLines, predErrLines, srcErrAbsLines, predErrAbsLines, \
        #     isConcretized, isExactMatch, corr_pred_rep_final = \
        #         runPerLine(srcCodeObj, srcLines, trgtLines, srcAbsLines, trgtAbsLines, errSet, lineNums, predAtK,
        #                    errInfo
        #                    , trgtErrAbsLines, actLineList, gold_repair_classes)
        #
        #     # Calculate accuracy and log it
        #     isLocated, isRelevant, isCompiled = calcAccuracy(actLinesStr, lineNums, \
        #                                                      trgtText, trgtErrAbsLines, predErrAbsLines, predErrLines,
        #                                                      predText)
        isCompiled, predText, repairLines, fin_Concretized, fin_indentFixed, fin_indentError, \
        isExactMatch, corr_pred_rep_final, predErrLines, lineNums, srcErrLines, srcErrAbsLines,\
        errSet, gold_repair_classes, repair_classes = \
            fixIncrementally(srcText, trgtText, srcID, trgtID, trgtErrAbsLines, actLinesStr, predAtK)
        results.append((row['id'], srcText, trgtText, predText, actLinesStr, utils.joinList(lineNums), \
                        row['sourceLineText'], utils.joinList(srcErrLines), trgtErrLines,
                        utils.joinLL(predErrLines), \
                        row['sourceLineAbs'], utils.joinLL(srcErrAbsLines), trgtErrAbsLines, errSet,
                        utils.toInt(fin_Concretized), utils.toInt(isExactMatch), utils.toInt(isCompiled)))
        if fin_indentError and fin_indentFixed:
            indentationErrorsFixed += 1

        #########################[  ERROR STATS  ]##########################

        # errorAbs = errInfo.getAbs()
        # if errInfo_dict.get(errorAbs, None) is None:
        #     errInfo_dict[errorAbs] = {'exact_match': 0, 'compiled': 0,
        #                               'not_compiled': 0, 'zero_shot_exact_match': 0,
        #                               'zero_shot_compiled': 0, 'zero_shot_not_compiled': 0
        #                               }
        # errInfo_dict[errorAbs]['exact_match'] += int(isExactMatch is True)
        # errInfo_dict[errorAbs]['compiled'] += int(isCompiled is True)
        # errInfo_dict[errorAbs]['not_compiled'] += 1 - int(isCompiled is True)

        ####################################################################


        if not isCompiled:
            not_compiled += 1
            print("{}/{}".format(not_compiled, i), end="")


        if corr_pred_rep_final:
            repair_class_pred += 1
        seen = False
        for gold_class in gold_repair_classes:
            if gold_class in repair_class_freq_dict.keys():
                seen = True
                repair_class_freq_dict[gold_class] += 1
                if isCompiled:
                    repair_class_repair_dict[gold_class] += 1
                if isExactMatch:
                    repair_class_exact_dict[gold_class] += 1
        if not seen:
            zero_shot += 1
            if isCompiled:
                zero_shot_compiled += 1
                print("{} zsc:{}/{}".format(i, zero_shot_compiled, zero_shot), end="")
            else:
                print(" zsnc:{}/{}".format(zero_shot - zero_shot_compiled, zero_shot), end="")
            if isExactMatch:
                zero_shot_exact += 1
        if not isCompiled or not seen:
            print()

        # if i != 0 and i % 100 == 0:
        #     print('\t...', i, '/', len(df), 'Completed')
        #     # break
        # if i >= no_of_eg:
        #     break

    endTime = timer()

    #########################[  ERROR STATS  ]##########################

    errInfo_df = pd.DataFrame(errInfo_dict.values(),
                              columns=['exact_match', 'compiled', 'not_compiled',
                                       'zero_shot_exact_match', 'zero_shot_compiled',
                                       'zero_shot_not_compiled'],
                              index=errInfo_dict.keys())
    errInfo_df.to_csv(errInfo_filePath + ".csv")

    ####################################################################

    print('\n#Programs=', len(df), 'Time Taken=', round(endTime - startTime, 2), '(s)')
    print("More than 1 line ", str(more_than_one_line))
    print("Indentation {}/{}".format(indentationErrorsFixed, totalIndentationErrs))

    ################################################################################

    for item in err_class_dict.items():
        print(item[0], " -> ", item[1])

    micro_data_dir = "./micro_data"
    full_path = os.path.join(micro_data_dir)
    # print(full_path)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    tmp_list = []
    for gc in repair_class_freq_dict.keys():
    # print("{} -> {}, {} out of {}".format(str(gc).replace("\n", "  "),
    #                                       (repair_class_repair_dict.get(gc, 0) / repair_class_freq_dict[gc]),
    #                                       (repair_class_exact_dict.get(gc, 0) / repair_class_freq_dict[gc]),
    #                                       repair_class_freq_dict[gc]))
        tmp_list.append([gc, repair_class_type_dict[gc], repair_class_freq_dict[gc], repair_class_repair_dict[gc],
                         repair_class_exact_dict[gc]])
    micro_data = pd.DataFrame(tmp_list, columns=['repair_class', 'repair_type', 'total_examples',
                                                 'repaired_examples', 'exact_matches'])
    micro_data.to_csv(
        micro_data_dir + "/micro_measures_data_" + str(predAtK) + "_" + str(os.path.split(dir_name)[1]) + ".csv")

    ################################################################################
    return pd.DataFrame(results, columns=columns), err_lines_ratio, tot_extra_err_lines, zero_shot, \
           zero_shot_compiled, zero_shot_exact, repair_class_pred


def runTest(fname, predAtK):
    df_data = pd.read_csv(fname, encoding="ISO-8859-1")
    no_of_eg = df_data.shape[0]
    print("using ", Globals.dir_name, df_data.shape)
    df_results, err_lines_ratio, tot_extra_err_lines, zero_shot, \
    zero_shot_compiled, zero_shot_exact, repair_class_pred = \
        run(df_data, predAtK)
    df_results.to_csv(resultsPred_filePath + str(predAtK) + '.csv')

    print('-' * 20, '\n', 'Pred@', str(predAtK) + '\n' + '-' * 20, '\n')
    print('Repair accuracy:', round(df_results['isCompiled'].mean(), 3))
    slash = os.sep
    output_file = os.path.abspath('..' + slash + 'output' + slash + 'Results.txt')
    with open(output_file, "a") as file:
        file.write("Date: " + str(datetime.now()) + "\n")
        file.write("Config: no_of_eg = " + str(no_of_eg)
                   + " k = " + str(predAtK) + " " + str(sys.argv[1]) + " localize: " + str(use_compiler_msg) +
                   " type info: " + str(Globals.inferTypes) + " more_data: " + str(Globals.more_data) + " new data"
                   + str(new_data) + " merged: " + str(merged) +  "\n\n")

        # file.write("\nRepair class acc " + str(rep_cls_acc) + "\n")
        # file.write('Correction Class Prediction Time:' + str(myGlobals.corr_cls) + "\n")
        # file.write('Reranking Time:' + str(myGlobals.rerank) + "\n")
        # file.write('Bigram Ranking Time:' + str(myGlobals.bigram_rank) + "\n")
        # file.write('Fixing Time:' + str(myGlobals.fixer) + "\n")
        file.write('Error-Localization:' + str(activeLocalization) + "\n")
        # file.write('Localization accuracy:' + str(round(df_results['isLocated'].mean(), 2)) + "\n")
        # file.write('Prediction accuracy:' + str(round(df_results['isRelevant'].mean(), 2)) + "\n")
        file.write('Exact Match accuracy:' + str(round(df_results['isExactMatch'].mean(), 4)) + "\n")
        file.write('Concretization accuracy:' + str(round(df_results['isConcretized'].mean(), 2)) + "\n")
        file.write('Repair accuracy:' + str(round(df_results['isCompiled'].mean(), 4)) + "\n")
        file.write('Err lines ratio:' + str(
            str(round(mean(err_lines_ratio), 4)) if len(err_lines_ratio) > 0 else str(0)) + "\n")
        file.write('total extra error lines:' + str(tot_extra_err_lines) + "\n")
        file.write('Repair class correctly predicted:' + str(repair_class_pred) + "\n")
        file.write('Zero shot cases:' + str(zero_shot) + "\n")
        file.write('Zero shot compiled:' + str(zero_shot_compiled) + "\n")
        file.write('Zero shot exact:' + str(zero_shot_exact) + "\n\n")
        # file.write('Repair class accuracy:' + str(round(repair_class_acc, 4)) + "\n\n")


def string_escape(s, encoding='utf-8'):
    return (s.encode('latin1')  # To bytes, required by 'unicode-escape'
            .decode('unicode-escape')  # Perform the actual octal-escaping decode
            .encode('latin1')  # 1:1 mapping back to bytes
            .decode(encoding))  # Decode original encoding

def reset_timers():
    Globals.abstraction = 0
    Globals.concretization = 0
    Globals.compile_freq = 0
    Globals.compile_time = 0
    Globals.predict = 0
    Globals.indent = 0


def repairProgram(fname, predAtK, source=''):
    if source == "":
        if fname == "":
            # This can be the case when a new file is created in vscode (it doesn't yet have a name)
            return [], [], False, [], [], []
        srcText = open(fname).read()
    else:
        srcText = string_escape(source)
    predAtK = int(predAtK)
    # Parse the source/erroneous code
    srcCodeObj = Code(srcText)
    srcLines = srcText.splitlines()
    srcLinesOld = deepcopy(srcLines)

    reset_timers()

    errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)

    # sourceCode = Code(srcText)
    initErrInfo = srcCodeObj.getErrorInfo()
    repair_classes = []
    isCompiled, predText, repairLines, fin_Concretized, fin_indentFixed, fin_indentError, \
    isExactMatch, corr_pred_rep_final, predErrLines, lineNums, srcErrLines, srcErrAbsLines, \
    errSet, gold_repair_classes, repair_class_dict = \
        fixIncrementally(srcText, '', 0, 0, '', '', predAtK)
    # print('-' * 20 + '\nOriginal Code\n' + '-' * 20 + '\n' + srcText)
    # print('-' * 20 + '\nMACER\'s Repair\n' + '-' * 20 + '\n' + predText)
    compiled = Code(predText).getErrorInfo().lineNo == -1
    # print('\nCompiled Successfully? ', compiled)
    # predLines = predText.splitlines()

    srcCodeObjOld = Code(srcLinesOld)
    start = timer()
    abstractConverter = AbstractConverter.AbstractConverter(srcCodeObjOld, inferTypes=inferTypes, debug=debug,
                                                            useAST=False)
    srcTokenizedCodeOld, srcAbsLinesOld, srcSymbTableOld = abstractConverter.getAbstractionAntlr()
    srcLinesOld = utils.joinLL(AbstractHelper.getPlainCodeFromTokenizedCode(srcTokenizedCodeOld)).splitlines()
    Globals.abstraction += timer() - start

    predCodeObj = Code(predText)
    start = timer()
    abstractConverter = AbstractConverter.AbstractConverter(predCodeObj, inferTypes=inferTypes, debug=debug,
                                                            useAST=False)
    predTokenizedCode, predAbsLines, predSymbTable = abstractConverter.getAbstractionAntlr()
    predLines = utils.joinLL(AbstractHelper.getPlainCodeFromTokenizedCode(predTokenizedCode), useConc=True).splitlines()
    Globals.abstraction += timer() - start

    correctedLines = []
    changeLines = []
    feedbacks = []
    allEditDiffs = []
    for j in range(min(len(srcLinesOld), len(predLines))):
        # srcLine = srcLinesOld[j]
        predLine = predLines[j]
        # alignDict = getAlignDict(srcLine, predLine)
        # if isinstance(alignDict, dict) and alignDict['editDistance'] > 0:

        srcLineTok = srcTokenizedCodeOld[j]
        predLineTok = predTokenizedCode[j]
        editDiffs = getLineDiff(srcLineTok, predLineTok)
        if len(editDiffs) > 0:
            correctedLines.append(j)
            changeLines.append(predLine)
            tmp_list = []
            tmp_list_feedback = []
            for rc_int in repair_class_dict.get(j+1, []):
                if rc_int == -1:
                    tmp_list.append("Indent fix")
                    msg1 = "Seems like something is wrong with Indentation."
                    msg2 = "Indentation in Python refers to the " \
                           "(spaces and tabs) that are used at the beginning of a line."
                    action = "insert"
                    actionMsg = "Try adding"
                    tokens = ["    "]
                    tokensText = ["INDENT"]
                    fullText = msg1 + " " + msg2
                    feedback = utils.convertFeedbacktoDict(Feedback(fullText, msg1, msg2, actionMsg, action,
                                                                    tokens, tokensText, ""))
                    tmp_list_feedback.append(feedback)
                else:
                    repair_class = new_encoder.inverse_transform([rc_int])[0]
                    tmp_list.append(repair_class)
                    feedback, hasName = getFeedbackFromRepairClass(repair_class)
                    feedback = utils.convertFeedbacktoDict(feedback)
                    tmp_list_feedback.append(feedback)

            allEditDiffs.append([utils.convertEditDiffToDict(ed) for ed in editDiffs])
            repair_classes.append(tmp_list)
            feedbacks.append(tmp_list_feedback)
    # print("pred ======================", predText)
    print("Concretization time ", Globals.concretization)
    print("Abstraction time", Globals.abstraction)
    print("Compile time , freq", Globals.compile_time, Globals.compile_freq)
    print("indent time", Globals.indent)
    print("Macer predict time ", Globals.predict)
    # print(changeLines)
    # print("Edit diffs", allEditDiffs)
    return correctedLines, changeLines, compiled, repair_classes, feedbacks, allEditDiffs


if __name__ == '__main__':
    predAtK = int(sys.argv[2])
    if sys.argv[1] == 'singleL':
        # if new_data:
        #
        # else:
        # fname = CF.fnameSingleL_Test_new
        fname = CF.fnameSingleL_Test_merged
        # fname = CF.fnameSingleL_Test
    # elif sys.argv[1] == 'deepfix':
    #     fname = CF.fnameDeepFix_Train
    # is_multi = True
    else:
        fname = sys.argv[1]
    if fname.split('.')[-1] == 'csv':
        runTest(fname, predAtK)
    elif fname.split('.')[-1] == 'py':
        print(repairProgram(fname, predAtK))
    else:
        print(
            "Expected .py file or .csv file as 2nd argument: python testRepair.py <dataset/path-to-test-file> <PredK>")

#         error_args()
# endregion
