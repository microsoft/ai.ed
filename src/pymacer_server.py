from flask import Flask, request
from ML.testRepair import repairProgram
from timeit import default_timer as timer
import json

app = Flask(__name__)


@app.route("/")
def home():
    return {"PyMACER"}


@app.route("/getfixes", methods=["POST"])
def getFixes():
    fname = ""
    predAtk = 5
    source = request.get_json(force=True)["source"]
    start = timer()
    lineNums, predLines, compiled, repair_classes, feedbacks, editDiffs = repairProgram(
        fname, predAtk, source
    )
    print("predict time ", timer() - start)
    return_dict = {}
    lineRepairs = []
    for i in range(len(predLines)):
        repair = dict()
        repair["lineNo"] = lineNums[i]
        repair["repairLine"] = predLines[i]
        repair["repairClasses"] = repair_classes[i]
        repair["feedback"] = feedbacks[i]
        repair['editDiffs'] = editDiffs[i]
        lineRepairs.append(repair)
    return_dict["repairs"] = lineRepairs
    return_value = json.dumps(return_dict)
    print(return_value)

    return return_value.encode("utf-8")


if __name__ == "__main__":
    app.run()