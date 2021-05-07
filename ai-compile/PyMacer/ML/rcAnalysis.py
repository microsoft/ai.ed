from difflib import SequenceMatcher

from AntlrGrammar.Python3Parser import Python3Parser
from ML.Globals import ins_encoder, del_encoder, repl_encoder, rest_encoder
from Symbolic import DataStructs, AbstractHelper
from Symbolic.ConcreteToken import LITERALS, TYPE_SYMB
from Symbolic.DataStructs import EditDiff

SPECIAL_TOKENS = ['LITERAL', 'NAME', 'SKIP_', 'UNKNOWN_CHAR', 'NEWLINE', 'INDENT', 'DEDENT']
def getConcreteToken(trgtAbs):
    '''Mainly, handle literals or type abstractions.
    For rest, just substitute using Python3Parser'''

    spell = trgtAbs
    if str(trgtAbs) in LITERALS:
        return "LITERAL"

    if trgtAbs.startswith(TYPE_SYMB) or trgtAbs == 'NAME':
        return "NAME"


    # If neither Literal, nor type, return abstract itself (probably punctuation/keyword/BUILIN_FUNC/SPECIALS)
    if trgtAbs in Python3Parser.symbolicNames:
        ind = Python3Parser.symbolicNames.index(trgtAbs)

        if ind < len(Python3Parser.literalNames): # len(literalNames) = 96, len(symbolicNames) = 99
            spell = Python3Parser.literalNames[ind][1:-1] # Remove leading and trailing inverted quotes
            if spell in DataStructs.KEYWORDS:
                return "KEYWORD"
            if spell == "INVALID":
                if trgtAbs == "NEWLINE":
                    return 'NEWLINE'

                # TODO: "NAME", "STRING_LITERAL", "BYTES_LITERAL", "DECIMAL_INTEGER", "OCT_INTEGER",
                # "HEX_INTEGER", "BIN_INTEGER", "FLOAT_NUMBER", "IMAG_NUMBER"
                return spell
        if trgtAbs == "INDENT":
            return 'INDENT'
        if trgtAbs == "DEDENT":
            return 'DEDENT'

    return spell

def getRepairClassType(repair_class):
    if repair_class in ins_encoder.classes_:
        return "insert"
    if repair_class in del_encoder.classes_:
        return "delete"
    if repair_class in repl_encoder.classes_:
        return "replace"
    if repair_class in rest_encoder.classes_:
        return "rest"

def getFeedbackFromRepairClass(repair_class):
    add = []
    dl = []
    for token in repair_class.split("\n"):
        if token.startswith('-'):
            dl.append(token[2:])
        elif token.startswith('+'):
            add.append(token[2:])

    tok_add = ""
    tok_dl = ""
    names = ""
    hasLiteral = False
    hasName = False
    otherSpecial = False
    for token in add:
        conc_token = getConcreteToken(token)
        if conc_token == "LITERAL":
            hasLiteral = True
        elif conc_token == "NAME":
            hasName = True
        elif conc_token in SPECIAL_TOKENS:
            otherSpecial = True
        else:
            tok_add += token + " (\'" + conc_token + "\'), "
    tok_add = tok_add[:-2]

    for token in dl:
        conc_token = getConcreteToken(token)
        if conc_token == "LITERAL":
            hasLiteral = True
        elif conc_token == "NAME":
            hasName = True
        elif conc_token in SPECIAL_TOKENS:
            otherSpecial = True
        else:
            tok_dl += token + " (\'" + conc_token + "\'), "
    tok_dl = tok_dl[:-2]

    repair_type = getRepairClassType(repair_class)

    feedback = "Seems like there was some error on this line. "
    if repair_type == "insert":
        if len(tok_add) > 0:
            feedback += "You seem to be missing some token(s). "
            feedback += "Try adding - " + tok_add + "."
    if repair_type == "delete":
        if len(tok_dl) > 0:
            feedback += "Your use of the some token(s) may be causing problems. Try removing these "
            feedback += "-" + tok_dl + "."
    if repair_type == "replace":
        if len(tok_add) != 0 or len(tok_dl) != 0:
            feedback += "Your use of the some token(s) may be causing problems. "
        if len(tok_dl) > 0:
            feedback += "Try replacing these " + "-" + tok_dl + " - with something else."

    if repair_type == "rest":
        feedback += "It seems there are multiple issues with line. "
        if len(tok_dl) > 0:
            feedback += "Try deleting these token(s) - " + tok_dl + "."
        if len(tok_add) > 0:
            feedback += " You may try to add some of these token(s) - " + tok_add + "."

    if hasLiteral:
        feedback += "There seems to be some issue with literals (Literals are used to represent " \
                    "fixed values like 0, True, False, 'string' etc). Did you forget a quote (\")?"

    # if hasName:
    #     feedback += "Seems like there is some issue with variable "

    return feedback, hasName


def getLineDiff(srcLine, trgtLine):
    x = AbstractHelper.getAbstractLineFromTokenizedLine(srcLine)
    # x = srcLine.split(' ')
    y = AbstractHelper.getAbstractLineFromTokenizedLine(trgtLine)
    # y = trgtLine.split(' ')
    sm = SequenceMatcher(None, x, y)

    editDiffs = []
    if len(x) == 0 and len(y) != 0:
        tokenStr = ""
        for t in range(len(y)):
            token = trgtLine[t].text
            tokenStr += token + " "
        tokenStr = tokenStr[:-1]
        tmpEditDiff = EditDiff("insert", 0, 0, tokenStr)
        editDiffs.append(tmpEditDiff)
        return editDiffs

    if len(y) == 0 and len(x) != 0:
        end = srcLine[len(x) - 1].column + len(srcLine[len(x) - 1].text) - 1
        tmpEditDiff = EditDiff("delete", 0, end)
        editDiffs.append(tmpEditDiff)
        return editDiffs
    # SequenceMatcher.get_opcodes() -  https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher.get_opcodes
    for opcodes in sm.get_opcodes():
        if opcodes[0] == 'equal':
            continue
        elif opcodes[0] == 'replace':
            start = srcLine[opcodes[1]].column
            end = srcLine[opcodes[2] - 1].column + len(srcLine[opcodes[2] - 1].text) - 1
            tokenStr = ""
            for t in range(opcodes[3], opcodes[4]):
                token = trgtLine[t].text
                tokenStr += token + " "
            tokenStr = tokenStr[:-1]
            tmpEditDiff = EditDiff("replace", start, end, tokenStr)
            editDiffs.append(tmpEditDiff)
        elif opcodes[0] == 'insert':
            index = opcodes[1]
            if opcodes[1] == len(srcLine):
                index = index - 1
                start = srcLine[index].column + len(srcLine[index].text) - 1
            else:
                start = srcLine[index].column

            end = start
            tokenStr = ""
            for t in range(opcodes[3], opcodes[4]):
                token = trgtLine[t].text
                tokenStr += token + " "
            tokenStr = tokenStr[:-1]
            tmpEditDiff = EditDiff("insert", start, end, tokenStr)
            editDiffs.append(tmpEditDiff)
        elif opcodes[0] == 'delete':
            start = srcLine[opcodes[1]].column
            end = srcLine[opcodes[2] - 1].column + len(srcLine[opcodes[2] - 1].text) - 1
            tmpEditDiff = EditDiff("delete", start, end)
            editDiffs.append(tmpEditDiff)

    return editDiffs