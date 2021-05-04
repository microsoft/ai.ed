from flask import Flask, request
from ML.testRepair import repairProgram
from timeit import default_timer as timer
import json
app = Flask(__name__)


@app.route("/")
def home():
    return {"Hello": "World"}


@app.route("/getfixes", methods=['POST'])
def getFixes():
    # print("here ", repr(request.form), repr(request.get_json(force=True)), repr(request.args))
    fname = ''
    predAtk = 5
    source = request.get_json(force=True)["source"]
    start = timer()
    lineNums, predLines, compiled, repair_classes, feedbacks, editDiffs \
        = repairProgram(fname, predAtk, source)
    print("predict time ", timer() - start)
    return_dict = []
    for i in range(len(predLines)):
        tmp_dict = dict()
        tmp_dict['lineNo'] = lineNums[i]
        tmp_dict['repairLine'] = predLines[i]
        tmp_dict['repair_classes'] = repair_classes[i]
        tmp_dict['feedbacks'] = feedbacks[i]
        # tmp_dict['editDiffs'] = editDiffs[i]
        return_dict.append(tmp_dict)
    return_value = json.dumps(return_dict)
    print(return_value)


    return return_value.encode("utf-8")

if __name__ == "__main__":
    app.run()
