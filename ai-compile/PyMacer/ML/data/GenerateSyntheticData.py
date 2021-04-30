import copy
import warnings
from collections import Counter
from datetime import datetime

from Symbolic import AbstractConverter, ConcreteConverter, AbstractHelper, ConcreteHelper

warnings.filterwarnings('ignore')
import keras
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.multiclass import OneVsRestClassifier
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from difflib import ndiff,Differ,SequenceMatcher
from timeit import default_timer as timer
from Common import ConfigFile as CF, utils
from Symbolic.DataStructs import *
from Symbolic import ClusterError

# if len(sys.argv)!=2:
#     print("Usage python train.py <path-to-train-data>")
#     sys.exit(1)

wo_err_id = True
debug = False
inferTypes = False
new_data = True
merged = True


if merged and new_data:
    print("Chose any one of merged or new data")
    exit()

if wo_err_id:
    print("wo_err_id")
if inferTypes:
    print('inferTypes')
if new_data:
    print("new_data")
if merged:
    print("merged")


if new_data:
    file_name = CF.fnameSingleL_Train_new
elif merged:
    file_name = CF.fnameSingleL_Train_merged
else:
    file_name = CF.fnameSingleL_Train
data=pd.read_csv(file_name,encoding='latin')
AllErrs = ClusterError.getAllErrs(CF.fname_newErrIDs)

tic = timer()
if inferTypes:
    srcColAbsName = 'sourceLineTypeAbs'
    trgtColAbsName = 'targetLineTypeAbs'
else:
    srcColAbsName = 'sourceLineAbs'
    trgtColAbsName = 'targetLineAbs'

length = len(data[srcColAbsName])

insert = [0] * length
delete = [0] * length
replace = [0] * length
nan_count = 0
# Find Repair Classes using DiffLib
for i in range(length):
    x_str = str(data[srcColAbsName][i])
    y_str = str(data[trgtColAbsName][i])
    if x_str == "nan":
        x_str = ""
    if y_str == "nan":
        y_str = ""
    x = x_str.split(' ')
    y = y_str.split(' ')
    sm=SequenceMatcher(None,x,y)
    repl_str=[]
    del_str=[]
    ins_str=[]
    for opcodes in sm.get_opcodes():
        if opcodes[0]=='equal':
            continue
        elif opcodes[0]=='replace':
            tmp_str=''
            for st in x[opcodes[1]:opcodes[2]]:
                tmp_str+='- '+ st + '<===>'
            for st in y[opcodes[3]:opcodes[4]]:
                tmp_str+='+ '+st + '<===>'
            repl_str.append(tmp_str[:-5])
        elif opcodes[0]=='insert':
            tmp_str=''
            for st in y[opcodes[3]:opcodes[4]]:
                tmp_str+='+ '+st + '\n'
            ins_str.append(tmp_str[:-1])
        elif opcodes[0]=='delete':
            tmp_str=''
            for st in x[opcodes[1]:opcodes[2]]:
                tmp_str+='- '+st + '\n'
            del_str.append(tmp_str[:-1])
    insert[i]=ins_str
    delete[i]=del_str
    replace[i]=repl_str
insert=np.array(insert)
delete=np.array(delete)
replace=np.array(replace)

errset=np.array(data['newErrSet'])
diffset=[]
for i in range(len(replace)):
    tmp_str=''
    tmp_str+=errset[i]+'\n'
    for repl in replace[i]:
        tmp_str+=repl+'\n'
    for dlt in delete[i]:
        tmp_str+=dlt+'\n'
    for ins in insert[i]:
        tmp_str+=ins+'\n'
    diffset.append(tmp_str[:-1])
diffset=np.array(diffset)

encoder=LabelEncoder()
labels=encoder.fit_transform(diffset)

one_hot_labels=keras.utils.to_categorical(labels)

counts=one_hot_labels.sum(axis=0)

del_items=[]
for i in range(len(counts)):
    if counts[i]<2:
        del_items.append(i)

del_indexes=one_hot_labels[:, del_items].any(1)

diffset=diffset[~del_indexes]

#################################################################
if wo_err_id:
    diffset_wo_err_ids = []
    err_ids = []
    for i in range(len(diffset)):
        tokens = "\n".join(diffset[i].split("\n")[1:])
        err_ids.append(diffset[i].split("\n")[0])
        diffset_wo_err_ids.append(tokens)

    print("diffset_wo_err_id_len" ,len(diffset_wo_err_ids))
    print("err_ids_len", len(err_ids))
    print("\nno of classes " + str(len(set(diffset_wo_err_ids))))
    diffset = np.array(diffset_wo_err_ids)
    print("\ndiffset shape "  +str(diffset.shape))

#############################################################
print("no of classes ", len(set(diffset)))
new_encoder = LabelEncoder()
new_int_labels = new_encoder.fit_transform(diffset)

new_labels=keras.utils.to_categorical(new_int_labels)



src_abs_lines = np.array(data[srcColAbsName])


tgt_abs_lines = np.array(data[trgtColAbsName])


src_abs_lines = src_abs_lines[~del_indexes]
tgt_abs_lines = tgt_abs_lines[~del_indexes]

insert=insert[~del_indexes]
delete=delete[~del_indexes]
replace=replace[~del_indexes]

errset=errset[~del_indexes]

coarse_one=[]
for i in range(len(src_abs_lines)):
    if replace[i]!=[] and insert[i]==[] and delete[i]==[]:
        coarse_one.append(1)
    else:
        coarse_one.append(0)


coarse_one=np.array(coarse_one)

noRepl_ind=np.where(coarse_one==0)
noRepl_diffset=diffset[noRepl_ind]
noRepl_replace=replace[noRepl_ind]
noRepl_delete=delete[noRepl_ind]
noRepl_insert=insert[noRepl_ind]


# lines only needing insert (1) , only delete (2) and misc (0)
coarse_two=[]
for i in range(len(noRepl_replace)):
    if noRepl_replace[i]==[] and noRepl_insert[i]!=[] and noRepl_delete[i]==[]:
        coarse_two.append(1)
    elif noRepl_replace[i]==[] and noRepl_insert[i]==[] and noRepl_delete[i]!=[]:
        coarse_two.append(2)
    else:
        coarse_two.append(0)
coarse_two=np.array(coarse_two)


repl_ind=np.where(coarse_one==1)
repl_diffset=diffset[repl_ind]

repl_encoder=LabelEncoder()
repl_int_labels=repl_encoder.fit_transform(repl_diffset)
repl_oh_labels=keras.utils.to_categorical(repl_int_labels)
print("repl_oh_shape", repl_oh_labels.shape)

ins_ind=np.where(coarse_two==1)
ins_diffset=noRepl_diffset[ins_ind]

ins_encoder=LabelEncoder()
ins_int_labels=ins_encoder.fit_transform(ins_diffset)
ins_oh_labels=keras.utils.to_categorical(ins_int_labels)
print("ins_oh_shape", ins_oh_labels.shape)


del_ind=np.where(coarse_two==2)
del_diffset=noRepl_diffset[del_ind]

del_encoder=LabelEncoder()
del_int_labels=del_encoder.fit_transform(del_diffset)
del_oh_labels=keras.utils.to_categorical(del_int_labels)
print("del_oh_shape", del_oh_labels.shape)

rest_ind=np.where(coarse_two==0)
rest_diffset=noRepl_diffset[rest_ind]

rest_encoder=LabelEncoder()
rest_int_labels=rest_encoder.fit_transform(rest_diffset)
rest_oh_labels=keras.utils.to_categorical(rest_int_labels)
print("rest_oh_shape", rest_oh_labels.shape)


feature_vector_all=[]
for i in range(len(src_abs_lines)):
    tmp_lst=[]
    tmp_err_set = str(errset[i])
    # if(i > 18000):
    #     print("here")
    if tmp_err_set == "nan":
        tmp_err_set = ""
    for err in tmp_err_set.split(' '):
        tmp_lst.append(err.split(';')[0])
    # for err in tmp_err_set.split(';'):
    #     tmp_lst.append(err)
    tmp_line_str = str(src_abs_lines[i])
    if tmp_line_str == "nan":
        tmp_line_str = ""
    tmp_line=tmp_line_str.split(' ')
    for abst in tmp_line:
        tmp_lst.append(abst)
    for ind in range(len(tmp_line)-1):
        tmp_lst.append(tmp_line[ind]+' '+tmp_line[ind+1])
    feature_vector_all.append(tmp_lst)
feature_vector_all=np.array(feature_vector_all)

tkn=keras.preprocessing.text.Tokenizer(filters='')
tkn.fit_on_texts(feature_vector_all)

feature_vector=[]
delete_src_lines = []
delete_tgt_lines = []
delete_class_labels_text = []
delete_class_labels_int = []
delete_at_indices = []
other_op = 0
for i in range(len(tgt_abs_lines)):
    if delete[i] != [] and insert[i] == [] and replace[i] == []:
        tmp_lst=[]
        tmp_err_set = str(errset[i])
        # if(i > 18000):
        #     print("here")
        if tmp_err_set == "nan":
            tmp_err_set = ""
        for err in tmp_err_set.split(' '):
            tmp_lst.append(err.split(';')[0])
        # for err in tmp_err_set.split(';'):
        #     tmp_lst.append(err)
        tmp_line_str = str(tgt_abs_lines[i])
        if tmp_line_str == "nan":
            tmp_line_str = ""
        tmp_line=tmp_line_str.split(' ')
        for abst in tmp_line:
            tmp_lst.append(abst)
        for ind in range(len(tmp_line)-1):
            tmp_lst.append(tmp_line[ind]+' '+tmp_line[ind+1])

        x = str(src_abs_lines[i])
        if x == "nan":
            x = ''
        x = x.split(' ')
        y = str(tgt_abs_lines[i])
        if y == "nan":
            y = ''
        y = y.split(' ')

        sm = SequenceMatcher(None, x, y)
        delete_indices = []
        for opcodes in sm.get_opcodes():
            if opcodes[0] == 'delete':
                for st in range(opcodes[1],opcodes[2]):
                    delete_indices.append(st)
            else:
                # print("Other opcode " + opcodes[0])
                if opcodes[0] == 'equal':
                    continue
                other_op += 1

        feature_vector.append(tmp_lst)
        delete_src_lines.append(src_abs_lines[i])
        delete_tgt_lines.append(tgt_abs_lines[i])
        delete_class_labels_text.append(diffset[i])
        delete_class_labels_int.append(del_encoder.transform([diffset[i]])[0])
        delete_at_indices.append(delete_indices)

feature_vector=np.array(feature_vector)

encoded_vec=tkn.texts_to_matrix(feature_vector)
delete_class_labels_int = np.array(delete_class_labels_int)
print("Stats : feature vector delete srclines , delete_tgt_lines, delete_class_labels, delete_at_indices")
print("Shapes : ", encoded_vec.shape, len(delete_src_lines), len(delete_tgt_lines), len(delete_class_labels_text), len(delete_at_indices))
print("Other ", other_op)
# print("delete class int : ", delete_class_labels_int)
# print("delete indices: " , delete_at_indices)
# for i in range(len(delete_at_indices)):
#     print(delete_tgt_lines[i], delete_src_lines[i])
#     print(delete_class_labels_text[i] , delete_at_indices[i])

print("Training OvA Classifiers...")


src_bigram_all=[]
for i in range(len(src_abs_lines)):
    tmp_lst=[]
    edit_lst=[]
    tmp_line_str = str(src_abs_lines[i])
    if tmp_line_str == "nan":
        tmp_line_str = ""
    tmp_line=tmp_line_str.split(' ')
    for ind in range(len(tmp_line)-1):
        tmp_str=''
        tmp_str+=tmp_line[ind]+' '+tmp_line[ind+1]
        tmp_lst.append(tmp_str)
    src_bigram_all.append(tmp_lst)

# src_bigram_all=np.array(src_bigram_all)

src_edits=[]
for i,line in enumerate(delete_tgt_lines):
    if isinstance(line, float):
        line = []
    tmp_edit=[0]*len(line)

    for j in range(len(line)):
        if j in delete_at_indices[i]:
            tmp_edit[j] = 1
    src_edits.append(tmp_edit)

src_bigram=[]
edit_bigram=[]
for i in range(len(delete_tgt_lines)):
    tmp_lst=[]
    edit_lst=[]
    tmp_line_str = str(delete_tgt_lines[i])
    if tmp_line_str == "nan":
        tmp_line_str = ""
    tmp_line=tmp_line_str.split(' ')
    for ind in range(len(tmp_line)-1):
        if src_edits[i][ind+1]==1:
            edit_lst.append(1)
        else:
            edit_lst.append(0)
        tmp_str=''
        tmp_str+=tmp_line[ind]+' '+tmp_line[ind+1]
        tmp_lst.append(tmp_str)
    src_bigram.append(tmp_lst)
    edit_bigram.append(edit_lst)

src_bigram_for_tkn = src_bigram + src_bigram_all
src_bigram_for_tkn = np.array(src_bigram_for_tkn)
src_bigram=np.array(src_bigram)
edit_bigram=np.array(edit_bigram)

edit_tkn = keras.preprocessing.text.Tokenizer(filters='')
edit_tkn.fit_on_texts(src_bigram_for_tkn)
encoded_bigram=edit_tkn.texts_to_matrix(src_bigram)

sparse_edit_pos=np.zeros((src_bigram.shape[0],len(edit_tkn.word_index)+1))
for i in range(src_bigram.shape[0]):
    if src_bigram[i]==[]:
        sparse_edit_pos[i][0]=1
    for j in range(len(src_bigram[i])):
        if edit_bigram[i][j]==1:
            idx=edit_tkn.word_index[src_bigram[i][j].lower()]
            sparse_edit_pos[i][idx]=1


def train_multiple_rankers(oh_labels,int_labels,bigram,edit_pos):
    models=[0]*oh_labels.shape[1]
    accuracies=[]
    glb_cnt=0
    test_cnt=0
    for i in range(oh_labels.shape[1]):
        models[i]=OneVsRestClassifier(DecisionTreeClassifier())
        train_X=bigram[np.where(int_labels==i)]
        train_Y=edit_pos[np.where(int_labels==i)]
        models[i].fit(train_X,train_Y)
#        print(i)
    return models,accuracies

print("Training flat rankers")
start = timer()
delete_class_labels_int_oh = keras.utils.to_categorical(delete_class_labels_int)
# models,acc = train_multiple_rankers(delete_class_labels_int_oh, delete_class_labels_int, encoded_vec, delete_class_labels_int)
delete_yesno_model = OneVsRestClassifier(DecisionTreeClassifier())
# delete_yesno_model = MLkNN(k=10)
delete_yesno_model.fit(encoded_vec,delete_class_labels_int_oh)
# X_train, X_test, y_train, y_test = train_test_split(encoded_vec, delete_class_labels_int_oh)
# delete_yesno_model.fit(X_train,y_train)
# y_predict = delete_yesno_model.predict(X_test).toarray()
# arg_max = np.argmax(y_predict, axis=1)
# arg_max_test = np.argmax(y_test,axis=1)
# equal = np.all(y_test == y_predict, axis=1)
# max = np.max(y_predict, axis=1)
# tmp = np.where(max == 0)
# zeros = np.sum(tmp)
# print(np.sum(equal))
# # print(arg_max)
# print(arg_max.shape)
# # print(np.sum(y_test, axis=1))
# print()


flat_rankers,flat_accuracies=train_multiple_rankers(delete_class_labels_int_oh,delete_class_labels_int,encoded_bigram,sparse_edit_pos)
end = timer()
idx_to_bigram={}
for key,val in edit_tkn.word_index.items():
    idx_to_bigram[val]=key
print("Stat2 : ")
print("edit tkn ", encoded_bigram.shape)
print("flat " , len(flat_rankers),sparse_edit_pos.shape)
print("time " , end - start)
# print("edit bigram ", edit_bigram)


# Check if all elements of list1 are there in list2
def counterSubset(list1, list2):
    c1, c2 = Counter(list1), Counter(list2)
    for k, n in c1.items():
        if n > c2[k]:
            return False
    return True


def create_feat_vector(src_line):
    tmp_feat_vector=[]
    tmp_lst=[]
    tmp_line = src_line
    # tmp_line=src_line.split(' ')
    for abst in tmp_line:
        tmp_lst.append(abst)
    for ind in range(len(tmp_line)-1):
        tmp_lst.append(tmp_line[ind]+' '+tmp_line[ind+1])
    tmp_feat_vector.append(tmp_lst)
    return tmp_feat_vector

def create_bigram(src_line):
    tmp_bigram=[]
    tmp_lst=[]
    tmp_line=src_line
    for ind in range(len(tmp_line)-1):
        tmp_str=''
        tmp_str+=tmp_line[ind]+' '+tmp_line[ind+1]
        tmp_lst.append(tmp_str)
    tmp_bigram.append(tmp_lst)
    return tmp_bigram


def get_predicted_bigrams(specific_prediction,idx_to_bigram):
    predicted_bigrams=[]
    for x in np.where(specific_prediction[0]==1)[0]:
        if idx_to_bigram.get(x)!=None:
            predicted_bigrams.append(idx_to_bigram[x])
        else:
            predicted_bigrams.append(-1)
    return predicted_bigrams

def get_predicted_edit_pos(predicted_bigrams,act_bigram):
    pred_edit_pos=[]
    for x in range(len(predicted_bigrams)):
        if predicted_bigrams[x]==-1:
            pred_edit_pos.append(-1)
            continue
        for y in range(len(act_bigram[0])):
            if predicted_bigrams[x]==act_bigram[0][y].lower():
                pred_edit_pos.append(y+1)
    return pred_edit_pos

out_df = data.copy()
# out_df = pd.DataFrame(columns=data.columns)
out_df["repair_class"] = ""
tot_count = 0
ins_count = 0
del_count = 0
repl_count = 0
n = 10

ins_class_dict = {}
repl_class_dict = {}
del_class_dict = {}
start_time = timer()
exp = 0
done = False

print("####################replace classes#####################")
for cls in repl_encoder.classes_:
    print(cls.replace('\n', ' \/ '))
print("####################insert classes#####################")
for cls in ins_encoder.classes_:
    print(cls.replace('\n', ' \/ '))
print("####################del classes#####################")
for cls in del_encoder.classes_:
    print(cls.replace('\n', ' \/ '))
print("####################rest classes#####################")
for cls in rest_encoder.classes_:
    print(cls.replace('\n', ' \/ '))
print("####################repair classes#####################")

############ To Generate insert,delete and replace classes examples
for t, row in data.iterrows():
    if done:
        break
    done = True
    try:
        if t % 10 == 0:
            print("At ",t,"/",data.shape[0])
        # if t > 30:
        #     break
        srcID, trgtID = str(row['id']), str(row['id'])
        srcText, trgtText = str(row['sourceText']), str(row['targetText'])
        trgtErrLines = str(row['targetLineText']).strip()

        trgtErrAbsLines =  str(row[trgtColAbsName]).strip()
        actLinesStr = str(row['lineNums_Abs'])
        # Parse the source/erroneous code
        srcCodeObj, trgtCodeObj = Code(srcText, codeID=srcID), Code(trgtText, codeID=trgtID)
        srcLines, trgtLines = srcText.splitlines(), trgtText.splitlines()
        # errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)
        # trgtAbsLines = utils.splitCode(str(row['targetAbs']))
        abstractConverter = AbstractConverter.AbstractConverter(trgtCodeObj, inferTypes=inferTypes, debug=debug)
        trgtTokenizedCode, trgtAbsLines, trgtSymbTable = abstractConverter.getAbstractionAntlr()

        abstractConverter = AbstractConverter.AbstractConverter(srcCodeObj, inferTypes=inferTypes, debug=debug)
        srcTokenizedCode, srcAbsLines, srcSymbTable = abstractConverter.getAbstractionAntlr()
        # srcAbsLines = AbstractWrapper.getProgAbstraction(srcCodeObj)
        # trgtAbsLines = AbstractWrapper.getProgAbstraction(trgtCodeObj)
        # tmp_line = []

        for j, ins_class in enumerate(ins_encoder.classes_):
            if ins_class_dict.get(ins_class,0) >= n:
                continue
            done = False
            if wo_err_id:
                tmp_diff = ins_class.split("\n")
            else:
                tmp_diff = ins_class.split("\n")[1:]
            add = []
            dl = []
            for token in tmp_diff:
                if token.startswith('-'):
                    dl.append(token[2:])
                elif token.startswith('+'):
                    add.append(token[2:])
            if dl != []:
                raise Exception("Incorrect Insert class")

            trgtAbsLines_tmp = copy.deepcopy(trgtAbsLines)
            for i, line in enumerate(trgtAbsLines_tmp):

                check = counterSubset(add, line)
                if check:
                    tmp_line = line.copy()
                    tmp_add = copy.deepcopy(add)
                    for c in tmp_line:
                        if c in tmp_add:
                            tmp_line.remove(c)
                            tmp_add.remove(c)
                    new_row = row.copy()

                    new_row[srcColAbsName] = " ".join(tmp_line)
                    new_row[trgtColAbsName] = " ".join(trgtAbsLines_tmp[i].copy())
                    new_row['lineNums_Abs'] = i + 1
                    trgtAbsLines_tmp[i] = tmp_line
                    # output.append(trgtAbsLines)

                    new_row['sourceAbs'] = utils.joinLL(trgtAbsLines_tmp)
                    new_row['repair_class'] = ins_class
                    predLines, predAbsLines = copy.deepcopy(trgtLines), copy.deepcopy(trgtAbsLines_tmp)
                    predAbsLines[i] = utils.joinList(tmp_line, joinStr=' ')

                    # Concretize the predicted abstract fix
                    predLine, tempIsConcretized = ConcreteConverter.attemptConcretization(srcCodeObj,
                                    srcTokenizedCode, srcSymbTable, tmp_line , i+1, debug=debug, inferTypes=inferTypes)

                    predLines[i] = utils.joinList(predLine, joinStr=' ')
                    new_row['sourceText'] = utils.joinList(predLines, joinStr='\n')
                    tmp_code = Code(utils.joinList(predLines, joinStr='\n'))
                    e_ids = ClusterError.getErrSet(AllErrs, tmp_code)
                    new_row['newErrSet'] = utils.joinList(e_ids, joinStr="; ")
                    if tempIsConcretized and (not (e_ids == set())):
                        out_df = out_df.append(new_row)
                        tot_count += 1
                        ins_count += 1
                        ins_class_dict[ins_class] = ins_class_dict.get(ins_class, 0) + 1
                        break

        for j, repl_class in enumerate(repl_encoder.classes_):
            # print("for ",j,repl_class)
            if repl_class_dict.get(repl_class, 0) >= n:
                continue
            done = False
            if wo_err_id:
                tmp_diff = repl_class.split("\n")
            else:
                tmp_diff = repl_class.split("\n")[1:]
            add = []
            dl = []
            add_str = []
            dl_str = []
            for repl_token in tmp_diff:
                add_tmp = ""
                dl_tmp = ""
                for token in repl_token.split("<===>"):
                    if token.startswith('-'):
                        dl.append(token[2:])
                        dl_tmp += token[2:] + " "
                    elif token.startswith('+'):
                        add.append(token[2:])
                        add_tmp += token[2:] + " "
                add_str.append(add_tmp[:-1])
                dl_str.append(dl_tmp[:-1])

            trgtAbsLines_tmp = copy.deepcopy(trgtAbsLines)
            if len(add) == len(dl):
                breakOuter = False
                for i, line in enumerate(trgtAbsLines_tmp):
                    check = counterSubset(add, line)
                    if check:
                        tmp_line = line.copy()
                        tmp_add = add.copy()
                        for x,c in enumerate(tmp_line):
                            if c in tmp_add:
                                index = add.index(c)
                                if index >= len(dl):
                                    breakOuter = True
                                    break
                                tmp_line[x] = dl[index]
                                tmp_add.remove(c)
                        if breakOuter:
                            break
                        new_row = row.copy()
                        new_row[srcColAbsName] = " ".join(tmp_line)
                        new_row[trgtColAbsName] = " ".join(trgtAbsLines_tmp[i].copy())
                        new_row['lineNums_Abs'] = i+1
                        trgtAbsLines_tmp[i] = tmp_line
                        # output.append(trgtAbsLines)

                        new_row['sourceAbs'] = utils.joinLL(trgtAbsLines_tmp)
                        new_row['repair_class'] = repl_class.replace("<===>","\n")
                        predLines, predAbsLines = copy.deepcopy(trgtLines), copy.deepcopy(trgtAbsLines_tmp)
                        predAbsLines[i] = utils.joinList(tmp_line, joinStr=' ')

                        # Concretize the predicted abstract fix
                        predLine, tempIsConcretized = ConcreteConverter.attemptConcretization(srcCodeObj,
                                  srcTokenizedCode, srcSymbTable, tmp_line , i+1, debug=debug, inferTypes=inferTypes)
                        predLines[i] = utils.joinList(predLine, joinStr=' ')
                        new_row['sourceText'] = utils.joinList(predLines,joinStr='\n')
                        tmp_code = Code(utils.joinList(predLines, joinStr='\n'))
                        e_ids = ClusterError.getErrSet(AllErrs, tmp_code)
                        new_row['newErrSet'] = utils.joinList(e_ids, joinStr="; ")
                        if tempIsConcretized and (not (e_ids == set())):
                            out_df = out_df.append(new_row)
                            tot_count += 1
                            repl_count += 1
                            repl_class_dict[repl_class] = repl_class_dict.get(repl_class, 0) + 1
                            break

            else:
                # continue
                breakOuter = False
                if len(add_str) != len(dl_str):
                    print("Exception in class " , repl_class)
                    continue
                for i, line in enumerate(trgtAbsLines_tmp):
                    check = counterSubset(add, line)
                    substr_check = True
                    line_str = " ".join(line)
                    for substr in add_str:
                        if line_str.find(substr) == -1:
                            substr_check = False
                            break
                    # if check:
                    #     print("here")
                    if check and substr_check:
                        tmp_line = line.copy()
                        tmp_line_str = " ".join(tmp_line)
                        # tmp_add = add.copy()
                        for x, substr in enumerate(add_str):
                            index = tmp_line_str.find(substr)
                            if index == -1:
                                breakOuter = True
                                break
                            new_str = tmp_line_str[:index] + dl_str[x] + tmp_line_str[index+len(substr):]

                            tmp_line_str = new_str
                        if breakOuter:
                            break
                        tmp_line = tmp_line_str.split(" ")
                        new_row = row.copy()
                        new_row[srcColAbsName] = tmp_line_str
                        new_row[trgtColAbsName] = " ".join(trgtAbsLines_tmp[i].copy())
                        new_row['lineNums_Abs'] = i + 1
                        trgtAbsLines_tmp[i] = tmp_line
                        # output.append(trgtAbsLines)

                        new_row['sourceAbs'] = utils.joinLL(trgtAbsLines_tmp)
                        new_row['repair_class'] = repl_class.replace("<===>","\n")
                        predLines, predAbsLines = copy.deepcopy(trgtLines), copy.deepcopy(trgtAbsLines_tmp)
                        predAbsLines[i] = utils.joinList(tmp_line, joinStr=' ')

                        # Concretize the predicted abstract fix
                        predLine, tempIsConcretized = ConcreteConverter.attemptConcretization(srcCodeObj,
                                  srcTokenizedCode, srcSymbTable, tmp_line , i+1, debug=debug, inferTypes=inferTypes)
                        predLines[i] = utils.joinList(predLine, joinStr=' ')
                        new_row['sourceText'] = utils.joinList(predLines,joinStr='\n')
                        tmp_code = Code(utils.joinList(predLines, joinStr='\n'))
                        e_ids = ClusterError.getErrSet(AllErrs, tmp_code)
                        new_row['newErrSet'] = utils.joinList(e_ids, joinStr="; ")
                        if tempIsConcretized and (not (e_ids == set())):
                            out_df = out_df.append(new_row)
                            tot_count += 1
                            repl_count += 1
                            repl_class_dict[repl_class] = repl_class_dict.get(repl_class, 0) + 1
                            break


        for j, del_class in enumerate(del_encoder.classes_):
            if del_class_dict.get(del_class,0) >= n:
                continue
            del_class_int = del_encoder.transform([del_class])[0]
            done = False
            if wo_err_id:
                tmp_diff = del_class.split("\n")
            else:
                tmp_diff = del_class.split("\n")[1:]
            add = []
            dl = []
            for token in tmp_diff:
                if token.startswith('-'):
                    dl.append(token[2:])
                elif token.startswith('+'):
                    add.append(token[2:])
            if add != []:
                raise Exception("Incorrect Delete class")

            trgtAbsLines_tmp = copy.deepcopy(trgtAbsLines)
            prog_done = False
            for i, line in enumerate(trgtAbsLines_tmp):
                enc_trgtAbsLine = create_feat_vector(line)
                enc_trgtAbsLine = tkn.texts_to_matrix(enc_trgtAbsLine)
                tmp_bigram = create_bigram(line)
                enc_tmp_bigram = edit_tkn.texts_to_matrix(tmp_bigram)
                # check = counterSubset(add, line)
                # Ask yesno model
                check = delete_yesno_model.estimators_[del_class_int].predict(enc_trgtAbsLine)[0]
                if check == 1:

                    edit_pos = np.zeros(shape=enc_tmp_bigram.shape)
                    ones = np.where(enc_tmp_bigram[0] == 1)
                    for one in ones[0]:
                        edit_pos[0][one] = flat_rankers[del_class_int].estimators_[one].predict(enc_tmp_bigram)
                    pred_bigrams = get_predicted_bigrams(edit_pos, idx_to_bigram)
                    where_to_edit = get_predicted_edit_pos(pred_bigrams, tmp_bigram)

                    start = timer()
                    where_to_edit = sorted(where_to_edit)
                    if len(where_to_edit) == 0:
                        continue
                    for x in range(len(where_to_edit)):
                        tmp_line= copy.deepcopy(line)
                        to_insert = " ".join(dl)
                        tmp_line.insert(where_to_edit[x], to_insert)
                        new_row = row.copy()
                        new_row[srcColAbsName] = " ".join(tmp_line)
                        new_row[trgtColAbsName] = " ".join(trgtAbsLines_tmp[i].copy())
                        new_row['lineNums_Abs'] = i + 1
                        trgtAbsLines_tmp[i] = tmp_line
                        # output.append(trgtAbsLines)

                        new_row['sourceAbs'] = utils.joinLL(trgtAbsLines_tmp)
                        new_row['repair_class'] = del_class
                        predLines, predAbsLines = copy.deepcopy(trgtLines), copy.deepcopy(trgtAbsLines_tmp)

                        ####
                        # predAbsLines[i] = H.joinList(tmp_line, joinStr=' ')

                        # Concretize the predicted abstract fix
                        predLine, tempIsConcretized = ConcreteConverter.attemptConcretization(srcCodeObj,
                              srcTokenizedCode, srcSymbTable, tmp_line , i+1, debug=debug, inferTypes=inferTypes)
                        predLines[i] = utils.joinList(predLine, joinStr=' ')
                        new_row['sourceText'] = utils.joinList(predLines, joinStr='\n')
                        tmp_code = Code(utils.joinList(predLines, joinStr='\n'))
                        e_ids = ClusterError.getErrSet(AllErrs, tmp_code)
                        new_row['newErrSet'] = utils.joinList(e_ids, joinStr="; ")
                        if tempIsConcretized and (not (e_ids == set())):
                            out_df = out_df.append(new_row)
                            tot_count += 1
                            del_count += 1
                            del_class_dict[del_class] = del_class_dict.get(del_class, 0) + 1
                            prog_done = True
                            break
                    if prog_done:
                        break
    except Exception as e:
        print("Exception ",e)
        exp += 1
        done = False

end_time = timer()
for item in ins_class_dict.items():
    print(str(item[0]),"->",item[1])

for item in repl_class_dict.items():
    print(str(item[0]),"->",item[1])

for item in del_class_dict.items():
    print(str(item[0]),"->",item[1])


############ Write to csv


drop_cols = ['sourceLineText', 'targetLineText', 'diffText_del'
             , 'diffText_ins', 'diffAbs_del'
             , 'diffAbs_ins',  'sourceErrorPrutor', 'lineNums_Text']
out_df = out_df.drop(drop_cols, axis=1)
# out_df.drop('assignID', axis=1)
out_df.to_csv('/'.join(file_name.split('/')[:-1]) + "/generated"+ file_name.split("/")[-1].split(".")[0] + str(datetime.now().strftime("%d_%m_%y")) + ".csv")

print("exception ",exp)
print("Total " , tot_count)
print("time ",end_time - start_time)
print("ins, del, repl count : ", ins_count, del_count, repl_count)
print("exceptions " , exp)


