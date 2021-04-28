# --- The 4 stooges (Equal, Ins, Del and Repl) ---
import re

from Symbolic import CigarSrcTrgt
from Symbolic import ConcreteToken

'''
    lineNo argument is not required but added to be consistent with other handle* methods
'''
def handleEquality(cst_indices, lineNo=None):
    '''If equal, add currToken spell. And increment both source & target abs counters by numAbs'''
    trgtToken = cst_indices.getCurr_SrcLine()
    cst_indices.incSrc(trgtToken, appendOther=False)  # Since both source and target consumed
    cst_indices.incTrgt(trgtToken, appendOther=False)  # Don't append source or target with blanks

    return [trgtToken]


'''
    lineNo argument is not required but added to be consistent with other handle* methods
'''
def handleDeletion(cst_indices, lineNo=None, appendOther=True):
    '''If deletion, don't add any target spell. Just increment source abs counters by numAbs'''
    trgtToken = cst_indices.getCurr_SrcLine()
    cst_indices.incSrc('',
                       appendOther)  # Target spell is empty (deletion), but append Source (deletion consumes source)

    return []  # Ignore trgtTokens, since Deletion. But consume that many numAbs


def handleInsertion(cst_indices, lineNo=None, appendOther=True):
    '''If insert, guess and append the spelling of predicted Abs. Inc only target-abs counter by 1'''
    trgtToken = ConcreteToken.guessConcreteSpell(cst_indices.getCurr_TrgtAbs(), cst_indices.srcTrgtCigar.symbTable,
                                                 lineNo)
    # print("insertion ", trgtToken)
    cst_indices.incTrgt(trgtToken, appendOther)  # Consume one target Abs (hence appendOther with blank)

    return [trgtToken]  # Consumed 1 target abstract token


def handleReplacement(cst_indices, lineNo=None):
    '''If Replace, perform Delete + Insert'''
    delTrgtTokens = handleDeletion(cst_indices, lineNo, appendOther=False)  # Since both source and target consumed
    insTrgtTokens = handleInsertion(cst_indices, lineNo,
                                    appendOther=False)  # Don't append source or target with blanks

    # Return "inserted" target tokens (since deleted ones are useless)
    # And the number of abstract tokens deleted, to inc freq count (since just one token inserted anyways)
    return insTrgtTokens  # Consume 1 target abstract token


# --- Concretize ---
'''
    Concretizes the given token using cst_indices (mainly symbTable) by calling the appropriate handle* 
    method depending on the compareOp (obtained using cigar)
'''
def concretizeCToken(cst_indices, lineNo):
    callFunc = None
    # printSrcTokenAbs(cst_indices)

    if cst_indices.compareOp == '=':
        callFunc = handleEquality

    elif cst_indices.compareOp == 'D':
        callFunc = handleDeletion

    elif cst_indices.compareOp == 'I':
        callFunc = handleInsertion

    elif cst_indices.compareOp == 'X':
        callFunc = handleReplacement

    else:
        raise Exception('No clue on how to handle this compareOp: {}'.format(cst_indices.compareOp))

    trgtTokens = callFunc(cst_indices, lineNo)
    cst_indices.decFreq()  # Consumed currNumAbs (matched) abstract tokens
    cst_indices.srcTrgtCigar.trgtLine.extend(trgtTokens)

    isConcretized = True
    for trgtToken in trgtTokens:
        # Cases apart from None are to handle malformed string literals
        if trgtToken is None or ConcreteToken.STR_LITERAL in trgtToken or ConcreteToken.STR_TYPE in trgtToken:
            isConcretized = False
    return isConcretized


'''
    Tries to concretize the given line (stored in srcTrgtCigar which is a CST_Params object)
'''
def concretizeLine(srcTrgtCigar, lineNo):
    isConcretized = True
    cst_indices = CigarSrcTrgt.CST_Indices(srcTrgtCigar)  # For every CToken, there can be one or more AbsTokens

    for freq, compareOp in re.findall('(\d+)(.)', srcTrgtCigar.cigar):  # Cigar eg: 13=1I2=1X5=
        # Alternating Frequency and Compare-Operator (=, I, D)
        cst_indices.freq, cst_indices.compareOp = int(freq), compareOp

        while cst_indices.freq > 0:  # 'freq' number of times, do what the compareOp says
            # Handle the conversion of currCToken to spell
            tempIsConcretized = concretizeCToken(cst_indices, lineNo)
            isConcretized = isConcretized and tempIsConcretized  # Don't use "and concretizeCToken(cst_indices)" - shortHand issue!

            if cst_indices.freq == freq:
                raise Exception('Cigar not consumed. Freq is the same. Infinite loop!')
            else:
                freq = cst_indices.freq
            # printIndicesSpell(cst_indices, trgtTokens)

    return isConcretized
