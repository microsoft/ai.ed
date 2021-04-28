import json
import sys, os
# insert at 1, 0 is the script path (or '' in REPL)

sys.path.insert(1, sys.argv[4])

from ML.testRepair import repairProgram
import socketserver
import socket
import time
from timeit import  default_timer as timer


def bytesToStr(line):
    if isinstance(line, str):
        return line
    else:
        return line.decode("utf-8")


def recvall(sock):
    BUFF_SIZE = 4096 # 4 KiB
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


class BrainTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("handling", self.client_address[0])
        fname = ''
        predAtk = int(bytesToStr(self.request.recv(2).strip()))
        source = bytesToStr(recvall(self.request))
        start = timer()
        lineNums, predLines, compiled, repair_classes, feedbacks, editDiffs\
            = repairProgram(fname, predAtk, source)
        print("predict time " , timer() - start)
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
        self.request.sendall(return_value.encode("utf-8"))


if sys.argv[1] == "MACER":
    ip = sys.argv[2]
    port = int(sys.argv[3])
    print("running ", ip, port)
    with socketserver.ThreadingTCPServer((ip, port), BrainTCPHandler) as server:
        server.serve_forever()
