import os, sys
# Need to add path pymacer's path to system path inorder to locate its modules.
sys_path = os.path.abspath("./pymacer/pymacer-vscode")
sys.path.insert(1, sys_path)
from ML.testRepair import repairProgram
from timeit import default_timer as timer


def getRepairs(source):
    """
        Method invokes PyMACER and returns its recommendations in a dictionary
    """
    fname = ""
    predAtk = 5
    lineNums, predLines, compiled, repair_classes, feedbacks, editDiffs = repairProgram(
        fname, predAtk, source
    )
    return_dict = {}
    lineRepairs = []
    for i in range(len(predLines)):
        tmp_dict = dict()
        tmp_dict["lineNo"] = lineNums[i]
        tmp_dict["repairLine"] = predLines[i]
        tmp_dict["repairClasses"] = repair_classes[i]
        tmp_dict["feedback"] = feedbacks[i]
        tmp_dict['editDiffs'] = editDiffs[i]
        lineRepairs.append(tmp_dict)
    return_dict["repairs"] = lineRepairs

    return return_dict
