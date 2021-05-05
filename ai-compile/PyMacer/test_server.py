import unittest
import pytest

import server


@pytest.fixture
def client():
    server.app.config["TESTING"] = True

    with server.app.test_client() as client:
        yield client


def test_syntaxerror_request(client):
    rv = client.post("/getfixes", json={"source": 'print("Hello world")'})
    assert False


def test_noerror_request(client):
    rv = client.post("/getfixes", json={"source": 'print("Hello world")'})
    assert False
