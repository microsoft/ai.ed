import unittest
import pytest
import json
import server


@pytest.fixture
def client():
    server.app.config["TESTING"] = True

    with server.app.test_client() as client:
        yield client


def test_syntaxerror_request(client):
    resp = client.post("/getfixes", json={"source": "name = int(input(\"Enter your name\"))\r\n"
                                                    "age = int(input(\"Enter your age\"))\r\n\r\n"
                                                    "print(\"Hello \", name)\r\n\r\n"
                                                    "if age >= 18:\r\n"
                                                    "    print(\"can vote\")\r\n"
                                                    "else age < 18:\r\n"
                                                    "    print(\"can't vote\")"})
    data = json.loads(resp.data)

    print(data)
    assert "repairs" in data
    assert len(data["repairs"]) == 1

    repairs = data["repairs"]
    assert "lineNo" in repairs[0]
    assert "repairLine" in repairs[0]
    assert "repairClasses" in repairs[0]
    assert "feedback" in repairs[0]
    # assert "editDist" in data[0]


def test_noerror_request(client):
    resp = client.post("/getfixes", json={"source": 'print("Hello world")'})
    data = json.loads(resp.data)
    print(data)
    assert "repairs" in data
    assert len(data["repairs"]) == 0