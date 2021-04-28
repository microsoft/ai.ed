# File from original Tracer/ Macer
from prettytable import PrettyTable

import edlib

START_ORD = ord('A')  # Start the unicode conversion (of ints), from this number


# --- Class Defs ---
class CST_Indices:
    '''Cigar Source Target Indices: Structure containing parameters and checks for the concretization func call below'''

    def __init__(self, srcTrgtCigar):
        self.iSrcAbs, self.iTrgtAbs = 0, 0
        self.freq, self.compareOp = 0, None

        self.srcTrgtCigar = srcTrgtCigar

    def incSrc(self, trgtSpell, appendOther=True):
        ''' . srcAbs is incremented by number of abstractions per cToken'''
        self.srcTrgtCigar.alignAppendSrc(self)
        if appendOther:
            self.srcTrgtCigar.alignAppendTrgtAbs(self, appendBlank=True)
            self.srcTrgtCigar.alignAppendTrgtLine(trgtSpell)

        self.iSrcAbs += 1  #

    def incTrgt(self, trgtSpell, appendOther=True):
        '''Increment target Abs counter by numAbs. Could be 1, or = num of absTokens per cToken'''
        self.srcTrgtCigar.alignAppendTrgtAbs(self)
        self.srcTrgtCigar.alignAppendTrgtLine(trgtSpell)
        if appendOther:
            self.srcTrgtCigar.alignAppendSrc(self, appendBlank=True)

        self.iTrgtAbs += 1

    def decFreq(self):
        # Handles how many times to loop
        if self.freq <= 0:
            raise Exception('No clue on how to handle freq = 0: {} '.format(self.freq))

        self.srcTrgtCigar.align_Cigar.append(self.compareOp)
        self.freq -= 1  # Since we are handling the currCToken (and hence all its currAbsTokens)

    def getCurr_SrcLine(self):
        return self.srcTrgtCigar.srcLine[self.iSrcAbs]

    def getCurr_SrcAbs(self):
        return self.srcTrgtCigar.srcAbs[self.iSrcAbs]

    def getCurr_TrgtAbs(self):
        return self.srcTrgtCigar.trgtAbs[self.iTrgtAbs]


class CST_Params:
    '''Cigar Source Target parameters: Passed back-and-forth during concretization'''

    def __init__(self, currID, srcLine, srcAbs, trgtAbs, cigar, symbTable):
        self.currID = currID
        self.srcLine = srcLine
        self.srcAbs = srcAbs
        self.trgtAbs = trgtAbs
        self.cigar = cigar
        self.symbTable = symbTable

        self.align_Cigar = []
        self.align_SrcAbs, self.align_TrgtAbs = [], []
        self.align_SrcLine, self.align_TrgtLine = [], []

        self.trgtLine = []

    def alignAppendSrc(self, cst_indices, appendBlank=False):
        srcAbs, srcLine = '', ''
        if not appendBlank:
            srcAbs, srcLine = cst_indices.getCurr_SrcAbs(), cst_indices.getCurr_SrcLine()
        self.align_SrcAbs.append(srcAbs)
        self.align_SrcLine.append(srcLine)

    def alignAppendTrgtAbs(self, cst_indices, appendBlank=False):
        trgtAbs = ''
        if not appendBlank:
            trgtAbs = cst_indices.getCurr_TrgtAbs()
        self.align_TrgtAbs.append(trgtAbs)

    def alignAppendTrgtLine(self, trgtSpell):
        self.align_TrgtLine.append(trgtSpell)

    def __str__(self):
        stri = ''
        stri += '\n  CurrID : {}'.format(self.currID)
        stri += '\n   Cigar : {}'.format(self.cigar)

        p = PrettyTable()
        for name, var in zip(['Cigar_i:', 'SrcAbs :', 'TrgtAbs:', 'SrcLine:', 'TrgtLine:'],
                             [self.align_Cigar, self.align_SrcAbs, self.align_TrgtAbs, self.align_SrcLine,
                              self.align_TrgtLine]):
            p.add_row([name] + var)

        # Use encode:utf-8 to handle non-ascii srcLines
        return stri + '\n' + p.get_string(header=False, border=False)


# --- Unicode ops ---
def addToDict(dictAbs_Unicode, absTokens):
    for absT in absTokens:
        absT_str = str(absT)
        if absT_str not in dictAbs_Unicode:
            dictAbs_Unicode[str(absT_str)] = chr(len(dictAbs_Unicode) + START_ORD)  # Skip START_ORD num of unicodes


def getUnicodeDicts(srcAbs, trgtAbs):
    dictAbs_Unicode = {}
    addToDict(dictAbs_Unicode, srcAbs)
    addToDict(dictAbs_Unicode, trgtAbs)
    dictUnicode_Abs = {value: key for (key, value) in dictAbs_Unicode.items()}

    return dictAbs_Unicode, dictUnicode_Abs


def getUnicodeStrs(dictAbs_Unicode, absTokens):
    return ''.join([dictAbs_Unicode[absT] for absT in absTokens])


# --- Get Cigar ---

def lineUp_SrcTrgAbs(srcAbs, trgtAbs):
    dictAbs_Unicode, dictUnicode_Abs = getUnicodeDicts(srcAbs, trgtAbs)
    srcAbsUni = getUnicodeStrs(dictAbs_Unicode, srcAbs)
    trgtAbsUni = getUnicodeStrs(dictAbs_Unicode, trgtAbs)

    if len(trgtAbsUni) == 0:  # If the target Abs is empty (edlib crashes, hence handle separately)
        if len(srcAbsUni) == 0:  # And if the source Abs is empty as well
            cigar = ''  # Nothing to do
        else:
            cigar = str(len(srcAbsUni)) + 'D'  # Else, delete all source Abs
    else:
        cigar = edlib.align(trgtAbsUni, srcAbsUni, task='path')['cigar']

    # print joinLL([(absT, ord(uni)) for absT, uni in dictAbs_Unicode.items()])
    return cigar
