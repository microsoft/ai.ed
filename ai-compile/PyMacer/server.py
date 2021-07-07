from flask import Flask, request
from PyMACERAdapater import getRepairs
import json

app = Flask(__name__)

@app.route("/")
def home():
    return {"Hello": "World"}


@app.route("/getfixes", methods=["POST"])
def getFixes():
    source = request.get_json(force=True)["source"]
    return_dict = getRepairs(source)
    return_value = json.dumps(return_dict)
    return return_value.encode("utf-8")


if __name__ == "__main__":
    app.run()
