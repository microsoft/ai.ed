import ast


class TypeInference:
    def __init__(self, symbTable, debug=True):
        self.symbTable = symbTable
        self.debug = debug
        self.boolConsts = {True, False}
        self.listFuncs = {'list', 'range'} # Builtin Methods guaranteed to return a list
        self.strFuncs = {'str', 'oct', 'input'}  # Builtin Methods guaranteed to return a str
        self.numFuncs = {'len', 'float', 'sum', 'int', 'abs', 'ord'}  # Builtin Methods guaranteed to return a int

    def getInferredType(self, value, single, lineNo):
        '''
        Method tries to infer types of given value on given lineNo
        :param value:
        :param single: if False only for declarations like - a,b = 1, 2
        :param lineNo:
        :return: Returns a list of infered type. Unless single is False the returned list will be of lenght 1 having
        the inferred type of given value. If single==False then returned list will have following structure.
            rlist[0] = structType (Basically one of V_LIST, V_SET, V_TUPLE and sometimes (don't know when) V_DICT)
            rList[1:] = list of list of strings representing inferred types
            eg: a, b, c, d = 1, (1,2), [1,2], 3
            rList = ['V_TUPLE', ['V_NUM'], ['V_TUPLE', 'V_NUM', 'V_NUM'], ['V_LIST', 'V_NUM', 'V_NUM'], ['V_NUM']]
        '''
        if isinstance(value, ast.Constant):
            # TODO: NOT tested. Basically since python 3.8+ ast.Num, ast.Str, ast.Bytes, ast.NameConstant and ast.Ellipse where replaced (but still supported) by ast.Constant
            typ = type(value.value)
            if isinstance(typ, int):
                return ["V_NUM"]
            elif isinstance(typ, str):
                return ["V_STR"]
            elif isinstance(typ, bool):
                return ["V_BOOL"]
            else:
                return ["-1"]
        elif isinstance(value, ast.Num):
            return ["V_NUM"]
        elif isinstance(value, ast.Str):
            return ["V_STR"]
        elif isinstance(value, ast.Name):
            return [self.symbTable.getLatestSymbFromSymTable(value.id, lineNo, self.symbTable.currScope,
                                                             self.symbTable.currLevel)]
        elif isinstance(value, ast.NameConstant):
            if value.value in self.boolConsts:
                return ["V_BOOL"]
            return ["-1"]
        elif isinstance(value, ast.Set):
            if single:
                return ["V_SET"]
            else:
                rval = ["V_SET"]
                for elt in value.elts:
                    rval.append(self.getInferredType(elt, single=False, lineNo=lineNo))
                return rval
        elif isinstance(value, ast.List):
            if single:
                return ["V_LIST"]
            else:
                rval = ["V_LIST"]
                for elt in value.elts:
                    rval.append(self.getInferredType(elt, single=False, lineNo=lineNo))
                return rval
        elif isinstance(value, ast.Tuple):
            if single:
                return ["V_TUPLE"]
            else:
                rval = ["V_TUPLE"]
                for elt in value.elts:
                    rval.append(self.getInferredType(elt, single=False, lineNo=lineNo))
                return rval
        elif isinstance(value, ast.Dict):
            return ["V_DICT"]
        elif isinstance(value, ast.ListComp):
            return ["V_LIST"]
        elif isinstance(value, ast.SetComp):
            return ["V_SET"]
        elif isinstance(value, ast.DictComp):
            return ["V_DICT"]
        elif isinstance(value, ast.BinOp):
            lType = self.getInferredType(value.left, single, lineNo=lineNo)
            if lType == ["-1"]:
                rType = self.getInferredType(value.right, single, lineNo=lineNo)
                return rType
            return lType
        elif isinstance(value, ast.UnaryOp):
            return self.getInferredType(value.operand, single, lineNo=lineNo)
        elif isinstance(value, ast.IfExp):
            lType = self.getInferredType(value.body, single, lineNo=lineNo)
            if lType == ["-1"]:
                rType = self.getInferredType(value.orelse, single, lineNo=lineNo)
                return rType
            return lType
        elif isinstance(value, ast.Compare):
            return ["V_BOOL"]
        elif isinstance(value, ast.Call):
            # TODO: Extract finding function name to different method
            func_name = ''
            if isinstance(value.func, ast.Name):
                func_name = value.func.id
            elif isinstance(value.func, ast.Attribute):
                func_name = value.func.attr
            else:
                # raise Exception("New case while parsing getInferedType func name found {}".format(type(value.func)))
                print("New case while parsing getInferedType func name found {}".format(type(value.func)))
                return ["-1"]
            if func_name in self.numFuncs:
                return ["V_NUM"]
            elif func_name in self.strFuncs:
                return ["V_STR"]
            elif func_name in self.listFuncs:
                return ["V_LIST"]
            elif func_name == "set":
                return ["V_SET"]
            elif func_name == "dict":
                return ["V_DICT"]
            else:
                if self.debug:
                    print("Can't infer type of func call {}".format(func_name))
                return ["-1"]
        else:
            if self.debug:
                print("Couldn't infer type {} ".format(type(value)))
            return ["-1"]
