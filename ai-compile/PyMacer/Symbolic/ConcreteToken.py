# File from original MACER/ TRACER some changes made to adapt to python
from Symbolic import DataStructs
from AntlrGrammar.Python3Parser import Python3Parser

# Literal types
STR_LITERAL = 'STRING'
NUM_LITERAL = 'NUMBER'
BOOL_LITERAL = 'V_BOOL'
LIST_LITERAL = 'V_LIST'
SET_LITERAL = 'V_SET'
DICT_LITERAL = 'V_DICT'
TUPLE_LITERAL = 'V_TUPLE'

TYPE_SYMB = 'V_' # All variables start with V_ (eg. V_NUM, V_STR etc)
STR_TYPE = 'V_STR' # Used to detect if concretization was successful especially for malformed strings

LITERALS = {STR_LITERAL, NUM_LITERAL, BOOL_LITERAL, LIST_LITERAL, DICT_LITERAL, SET_LITERAL, TUPLE_LITERAL}

'''
    Returns a basic Literal based on literalType
'''
def guessLiteral(literalType):
    '''Return a hard-code literal of matching type'''
    if literalType == NUM_LITERAL:
        return '0.0'
    elif literalType == STR_LITERAL:
        return "'string'"
    elif literalType == BOOL_LITERAL:
        return 'True'
    elif literalType == LIST_LITERAL:
        return '[]'
    elif literalType == SET_LITERAL:
        return '{}'
    elif literalType == DICT_LITERAL:
        return 'dict()'
    elif literalType == TUPLE_LITERAL:
        return '()'
    else:
        print("Couldn't guess literal type")
        return None


'''
    Uses symbTable to replace the variable with Most Recently Used same type variable
'''
def guessTypeKind(typeKind, symbTable, lineNo):
    '''Check SymbTable, and return a variable having typeKind'''
    return symbTable.getVarMatchingType(typeKind, lineNo)


'''
    Check if given token is added for rnn. Used only in tracer
'''
def checkRnnPreProcess(trgtAbs):
    if trgtAbs == '<start>':
        return '{'
    elif trgtAbs == '<stop>':
        return '}'
    return None


'''
    Method Tries to guess the concrete representation of the given trgtAbs text. Returns None if unsuccessful
'''
def guessConcreteSpell(trgtAbs, symbTable, lineNo):
    '''Mainly, handle literals or type abstractions.
    For rest, just substitute using Python3Parser'''

    spell = None
    # if trgtAbs == "\n":
    #     return trgtAbs
    if str(trgtAbs) in LITERALS:
        spell = guessLiteral(str(trgtAbs))

    elif trgtAbs.startswith(TYPE_SYMB) or trgtAbs == 'NAME':
        spell = guessTypeKind(trgtAbs, symbTable, lineNo)

    else:
        rnnPreProcess = checkRnnPreProcess(trgtAbs) # Not Used in Macer but using in Tracer

        if rnnPreProcess != None:
            spell = rnnPreProcess
        else:
            # If neither Literal, nor type, return abstract itself (probably punctuation/keyword/BUILIN_FUNC/SPECIALS)
            if trgtAbs in Python3Parser.symbolicNames:
                ind = Python3Parser.symbolicNames.index(trgtAbs)

                if ind < len(Python3Parser.literalNames): # len(literalNames) = 96, len(symbolicNames) = 99
                    spell = Python3Parser.literalNames[ind][1:-1] # Remove leading and trailing inverted quotes
                    if spell == "INVALID":
                        if trgtAbs == "NEWLINE":
                            spell =  '\n'
                        else:
                            # TODO: "NAME", "STRING_LITERAL", "BYTES_LITERAL", "DECIMAL_INTEGER", "OCT_INTEGER",
                            # "HEX_INTEGER", "BIN_INTEGER", "FLOAT_NUMBER", "IMAG_NUMBER"
                            spell = None
                elif trgtAbs == "INDENT":
                    spell = ' ' *DataStructs.INDENT_SIZE
                elif trgtAbs == "DEDENT":
                    spell = ''
                else: # probably one of "SKIP_" "UNKNOWN_CHAR"
                    spell = None
    # if spell == 'None':
    #     print('hi')
    #     pass
    return spell
