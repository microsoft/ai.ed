class SymbTable:

    def __init__(self, debug=True):
        self.symbTable = dict()
        self.symbTable[0] = dict({'global': dict({'scope_type': 'global', 'parent': None, 'scope_vars': dict()})})
        '''
            Structure of SymbTable:
            top level key : Level - Basically represent nesting level (incremented when function or class def is found)
            2nd Level key : scope name - represents the name of current scope (function/class name) or global
                    - values : scope_name (same as key), parent (name of parent scope), scope_vars (dict of variables
                            defined in this scope)
                3rd level (scope_vars) key: Name of variable or function (could be function call/def)
                                    value : dict with key as line no on which the var is used and value as a 
                                    dict containg abs_name (This dict is probably not necessary but is kept as is in 
                                    case more info needs to be stored in future) 
        '''
        self.currLevel = 0
        self.currScope = 'global'  # represents current scope
        self.defStack = ['global']  # Definition stack used to keep track of parent scopes
        self.lineToScope = dict()  # dict mapping lineNo to (level, scope) basically representing to which function the
        # given line belongs
        self.debug = debug

    '''
        Called when a new Scope definition (function or class) is found while parsing the ast.
        Updates the symbol table entries
    '''

    def enterScopeDef(self, funcName, type):
        self.currLevel += 1
        tmp_dict = self.symbTable.get(self.currLevel, dict())
        tmp_dict[funcName] = dict({'scope_type': type, 'parent': self.currScope, 'scope_vars': dict()})
        self.symbTable[self.currLevel] = tmp_dict
        self.currScope = funcName
        self.defStack.append(funcName)

    '''
        Called when the scope definition ends.
    '''

    def exitScopeDef(self):
        self.currLevel -= 1
        if len(self.defStack) == 1:
            raise Exception("Trying to pop global from def stack")
        self.defStack.pop()
        self.currScope = self.defStack[-1]

    '''
        Method called while parsing ast to save the abstraction information of key (token.text) at the given lineno
    '''

    def addToSymTable(self, key, lineno, value, tree_node=None, isClassVar=False):
        if isClassVar:
            lvl, enclosingScope = self.getEnclosingClassScope(self.currLevel, self.currScope)
            if enclosingScope is not None:
                tmp_dict = self.symbTable[lvl][enclosingScope]['scope_vars'].get(key, dict())
                tmp_dict[lineno] = value
                self.symbTable[lvl][enclosingScope]['scope_vars'][key] = tmp_dict
            else:
                # TODO: Maybe this logic shouldn't be here but instead caller should call getEnclosingScope
                #  and make this descision
                if tree_node is None:
                    return
                key = tree_node.value.id + "." + tree_node.attr
                tmp_dict = self.symbTable[self.currLevel][self.currScope]['scope_vars'].get(key, dict())
                tmp_dict[lineno] = value  # {'abs_name' : 'V_ATTR'}
                self.symbTable[self.currLevel][self.currScope]['scope_vars'][key] = tmp_dict
        else:
            tmp_dict = self.symbTable[self.currLevel][self.currScope]['scope_vars'].get(key, dict())
            tmp_dict[lineno] = value
            self.symbTable[self.currLevel][self.currScope]['scope_vars'][key] = tmp_dict

    def getEnclosingClassScope(self, level, scope):
        '''
        Method returns the level and scope name of enclosing CLASS scope of given scope. Raises an exception if the
        given scope is not enclosed in a class.
        :param level:
        :param scope:
        :return:
        '''
        if level == 0:
            # raise Exception('level 0 can\'t be enclosed in a class')
            return -1, None
        parent = self.symbTable[level][scope]['parent']
        parentType = self.symbTable[level - 1][parent]['scope_type']
        tmp_level = level - 1
        while tmp_level > 0 and parentType != 'CLASS':
            parent = self.symbTable[tmp_level][scope]['parent']
            parentType = self.symbTable[tmp_level - 1][parent]['scope_type']
            tmp_level -= 1
        if tmp_level == 0:
            # raise Exception('Scope {} at level {} is not enclosed in a class'.format(scope, level))
            print('Scope {} at level {} is not enclosed in a class'.format(scope, level))
            return -1, None
        return tmp_level, parent

    '''
        Takes id (textual representaion of NAME) and lineNo and returns the last valid abstract name used for this id.
        Valid means in the current or parent scope.
        Caution Only searches for use od id before(not including) the given line (statically)
    '''

    def getLatestSymbFromSymTable(self, id, lineNo, scopeName='', level=-1):
        if scopeName == '' or level == -1:
            if lineNo not in self.lineToScope.keys():
                if self.debug:
                    print("Scope and level not provided and line info also not found")
                return "-1"
            level = self.lineToScope[lineNo][0]
            scopeName = self.lineToScope[lineNo][1]
        if level in self.symbTable.keys():
            if scopeName in self.symbTable[level].keys():
                currScope = self.symbTable[level][scopeName]
                if id in currScope['scope_vars'].keys():
                    occurences = self.symbTable[level][scopeName]['scope_vars'][id]
                    mx = -1
                    mv = None
                    for k, v in occurences.items():
                        if mx < k < lineNo:
                            mx = k
                            mv = v
                    if mv is not None:
                        return mv['abs_name']
                # didn't find variable in current Scope, Check for parent scopes
                if scopeName != 'global':
                    return self.getLatestSymbFromSymTable(id, lineNo, currScope['parent'], level - 1)
        if self.debug:
            print("RHS variable not found previously {} ".format(id))
        return "-1"

    '''
        Returns a dict which currently just has abs_name for the token represented by text at the given lineNo.
    '''

    def getSymbAtLineNo(self, text, lineNo):
        if lineNo not in self.lineToScope.keys():
            return None
        level = self.lineToScope[lineNo][0]
        funcName = self.lineToScope[lineNo][1]
        funcVars = self.symbTable[level][funcName]['scope_vars']
        if text in funcVars.keys():
            varDetails = funcVars[text]
            if lineNo in varDetails.keys():
                return varDetails[lineNo]
        else:
            return None

    '''
        Get the Most Recently Used variable of the given type or NAME
    '''

    def getVarMatchingType(self, typeKind, lineNo):
        mn = None
        rval = None
        for lvl in self.symbTable.keys():
            for scope in self.symbTable[lvl].keys():
                for text in self.symbTable[lvl][scope]['scope_vars'].keys():
                    for line in self.symbTable[lvl][scope]['scope_vars'][text].keys():
                        tmp_dict = self.symbTable[lvl][scope]['scope_vars'][text][line]
                        abs_name = tmp_dict['abs_name']
                        if abs_name == typeKind and line <= lineNo and (mn is None or (lineNo - line) < mn):
                            rval = text
                            mn = lineNo - line
        return rval

    '''
        Utility Method to add line no details while parsing ast
    '''

    def addLineNoDetails(self, node):
        self.lineToScope[node.lineno] = (self.currLevel, self.currScope)

    def printSymbTable(self, indent=4):
        '''
        Utility method to print the symbTable
        :param indent:
        :return:
        '''
        for lvl in self.symbTable.keys():
            print("Level: {}".format(lvl))
            for scope in self.symbTable[lvl].keys():
                dc = self.symbTable[lvl][scope]
                print(
                    str(' ' * indent) + "Scope: {}, type: {}, parent {}".format(scope, dc['scope_type'], dc['parent']))
                for text in self.symbTable[lvl][scope]['scope_vars'].keys():
                    print(str(' ' * (2 * indent)) + "text: {}".format(text))
                    for line in self.symbTable[lvl][scope]['scope_vars'][text].keys():
                        tmp_dict = self.symbTable[lvl][scope]['scope_vars'][text][line]
                        print(str(' ' * (3 * indent)) + "line: {}, abs_name: {}".format(line, tmp_dict['abs_name']))

    def getLevelAndScope(self, lineno):
        if lineno in self.lineToScope.keys():
            return self.lineToScope[lineno][0], self.lineToScope[lineno][1]
        return -1, ''