import ast

from Symbolic.TypeInference import TypeInference


class PythonAstVisitor(ast.NodeVisitor):

    def __init__(self, symbTable, inferTypes=True, debug=True):
        super().__init__()
        self.symbTable = symbTable
        self.typeInference = TypeInference(symbTable, debug)
        self.debug = debug
        self.inferTypes = inferTypes

    def visit_Import(self, tree_node):
        '''
        tree_node represents a import name1 [as asname], name2 ... instruction. Method saves the name and asname
        information in the symbTable
        :param tree_node:
        :return:
        '''
        for module in tree_node.names:
            self.symbTable.addToSymTable(module.name, tree_node.lineno, {"abs_name": "MODULE"})
            if module.asname is not None:
                self.symbTable.addToSymTable(module.asname, tree_node.lineno, {"abs_name": "MODULE"})
        self.generic_visit(tree_node)

    def visit_ImportFrom(self, tree_node):
        '''
        tree_node represents a from name1 import n1 [as asname], n2 ... instruction. Important to note that only one
        module name (name1) can follow the from keyword.
        :param tree_node:
        :return:
        '''
        self.symbTable.addToSymTable(tree_node.module, tree_node.lineno, {"abs_name": 'MODULE'})
        for moduleEle in tree_node.names:
            self.symbTable.addToSymTable(moduleEle.name, tree_node.lineno, {"abs_name": "MODULE_ELE"})
            if moduleEle.asname != None:
                self.symbTable.addToSymTable(moduleEle.asname, tree_node.lineno, {"abs_name": "MODULE_ELE"})
        self.generic_visit(tree_node)

    def visit_FunctionDef(self, tree_node):
        '''
        tree_node represents a def name1(args): instruction. For now just saving the function name and ignoring the
        args. Also this instruction creates a new scope.
        :param tree_node:
        :return:
        '''
        self.symbTable.enterScopeDef(tree_node.name, "FUNCTION")
        self.symbTable.addToSymTable(tree_node.name, tree_node.lineno, {"abs_name": "FUNCTION_DEF"})
        self.generic_visit(tree_node)
        self.symbTable.exitScopeDef()


    def visit_Call(self, tree_node):
        '''
        tree_node represents a function call. Function could be a global function or a class method.
        :param tree_node:
        :return:
        '''
        func_name, success = self.getFuncName(tree_node)
        if success:
            self.symbTable.addToSymTable(func_name, tree_node.lineno, {"abs_name": "FUNCTION_CALL"})
        self.generic_visit(tree_node)


    def getFuncName(self, tree_node):
        '''
        Utility method to extract function name from tree_node.
        :param tree_node:
        :return:
        '''
        success = True
        if isinstance(tree_node.func, ast.Name):
            func_name = tree_node.func.id
        elif isinstance(tree_node.func, ast.Attribute):
            func_name = tree_node.func.attr
        else:
            # TODO: We might be able to fix this imporoper definitions directly
            if isinstance(tree_node.func, ast.Str) or isinstance(tree_node.func, ast.Call)\
                    or isinstance(tree_node.func, ast.Subscript):
                print("Improper definition of function on line {}".format(tree_node.lineno))
                func_name = ''
                success = False
            else:
                success = False
                raise Exception("New case while parsing call found {}".format(type(tree_node.func)))
        return func_name, success

    def visit_ClassDef(self, tree_node):
        '''
        tree_node represents a class definition. This is a scope instrution.
        :param tree_node:
        :return:
        '''
        self.symbTable.enterScopeDef(tree_node.name, "CLASS")
        self.symbTable.addToSymTable(tree_node.name, tree_node.lineno, {"abs_name": "CLASS_DEF"})
        self.generic_visit(tree_node)
        self.symbTable.exitScopeDef()

    def visit_Assign(self, tree_node):
        '''
        tree_node represents an assingn statement. This method uses TypeInference to determine what can be the type of
        name in the LHS.
        TODO: Also handle different types of assigns. (+=, -= etc)
        :param tree_node:
        :return:
        '''
        for target in tree_node.targets: # Loop is required for the case like : a = b = c = 10 (a, b and c are targets)
            # target = tree_node.targets[0]
            if isinstance(target, ast.Name):
                names = [target.id]
                value = tree_node.value
                if self.inferTypes:
                    inferredType = self.typeInference.getInferredType(value, single=True,lineNo=tree_node.lineno)
                else:
                    inferredType = ['NAME']

                if inferredType != ["-1"]:
                    self.symbTable.addToSymTable(names[0], tree_node.lineno, {'abs_name': inferredType[0]})

            if isinstance(target, ast.Attribute): # Class Vars
                names = []
                names.append(target.attr)
                value = tree_node.value
                if self.inferTypes:
                    inferredType = self.typeInference.getInferredType(value, single=True, lineNo=tree_node.lineno)
                else:
                    inferredType = ['NAME']

                if inferredType != ["-1"]:
                    self.symbTable.addToSymTable(names[0], tree_node.lineno, {'abs_name': inferredType[0]},
                                                 tree_node=target, isClassVar=True)
            elif isinstance(target, ast.Tuple): # To handle cases like a,b = 10, 'str'
                names = []
                for name in target.elts:
                    if isinstance(name, ast.Name):
                        names.append((name.id, 'name'))
                    elif isinstance(name, ast.Attribute):
                        names.append((name.attr, 'attr')) # Need to save this info to differentiate class vars from vars
                    else:
                        raise Exception("Unknown variable def found {}".format(type(name)))
                value = tree_node.value
                inferredType = []
                if self.inferTypes:
                    inferredType.extend(self.typeInference.getInferredType(value, single=False, lineNo=tree_node.lineno))
                    structType = inferredType[0]
                    inferredType = inferredType[1:]
                else:
                    inferredType = [['NAME']] * len(names)

                for i in range(min(len(names), len(inferredType))):
                    if self.debug:
                        print("{} -> {}".format(names[i], inferredType[i]))
                    if inferredType[i] != ["-1"]:
                        self.symbTable.addToSymTable(names[i][0], tree_node.lineno, {'abs_name': inferredType[i][0]},
                                                     tree_node=target.elts[i], isClassVar=True if names[i][1] == 'attr' else False)
        self.generic_visit(tree_node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        if hasattr(node, "lineno"):
            self.symbTable.addLineNoDetails(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)
