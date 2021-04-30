import warnings

warnings.filterwarnings('ignore')
import keras
import math
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from difflib import SequenceMatcher
import pickle
from sklearn.cluster import KMeans
from timeit import default_timer as timer

from Common import ConfigFile as CF

#
# if len(sys.argv)!=2:
#     print("Usage python train.py <path-to-train-data>")
#     sys.exit(1)

flags = {
    'merged': 16,
    'nd' : 8,
    'weid': 4,
    'md': 2,
    'ti': 1
}

# merged, nd, weid, md, ti
opt = int('10110', 2)

merged = opt & flags['merged']        # merged
new_data = opt & flags['nd']        # new data
wo_err_id = opt & flags['weid']     # w/o error id
more_data = opt & flags['md']       # more data
inferTypes = opt & flags['ti']      # using type inference

if merged and new_data:
    print("Chose any one of merged or new data")
    exit()

if wo_err_id:
    print("wo_err_id")
if more_data:
    print('more_data')
if inferTypes:
    print('inferTypes')
if new_data:
    print("new_data")
if merged:
    print("merged")
# data=pd.read_csv(sys.argv[1],encoding='latin')

if more_data:
    if new_data:
        file_name = CF.fnameSingleL_MoreData_Train_new
    elif merged:
        file_name = CF.fnameSingleL_MoreData_Train_merged
    else:
        file_name = CF.fnameSingleL_MoreData_Train
else:
    if new_data:
        file_name = CF.fnameSingleL_Train_new
    elif merged:
        file_name = CF.fnameSingleL_Train_merged
    else:
        file_name = CF.fnameSingleL_Train


data = pd.read_csv(file_name, encoding='latin')
errset = np.array(data['newErrSet'])


# Prepare the feature vector using the errset, unigrams and bigrams
def get_feature_vector(src_abs_lines, errset):
    feature_vector = []
    for i in range(len(src_abs_lines)):
        tmp_lst = []
        tmp_err_set = str(errset[i])
        if tmp_err_set == "nan":
            tmp_err_set = ""
        for err in tmp_err_set.split(' '):
            tmp_lst.append(err.split(';')[0])
        # for err in tmp_err_set.split(';'):
        #     tmp_lst.append(err)

        tmp_line_str = str(src_abs_lines[i])
        if tmp_line_str == "nan":
            tmp_line_str = ""
        tmp_line = tmp_line_str.split(' ')
        for abst in tmp_line:
            tmp_lst.append(abst)
        for ind in range(len(tmp_line) - 1):
            tmp_lst.append(tmp_line[ind] + ' ' + tmp_line[ind + 1])
        feature_vector.append(tmp_lst)
    feature_vector = np.array(feature_vector)
    return feature_vector


# Generate repair classes from data
def get_repair_classes(data):
    # global insert, delete, replace
    if inferTypes:
        length = len(data['sourceLineTypeAbs'])
    else:
        length = len(data['sourceLineAbs'])

    insert = [0] * length
    delete = [0] * length
    replace = [0] * length
    nan_count = 0
    # Find Repair Classes using DiffLib
    for i in range(length):
        if inferTypes:
            x_str = str(data['sourceLineTypeAbs'][i])
            y_str = str(data['targetLineTypeAbs'][i])
        else:
            x_str = str(data['sourceLineAbs'][i])
            y_str = str(data['targetLineAbs'][i])
        if x_str == "nan":
            x_str = ""
        if y_str == "nan":
            y_str = ""
        x = x_str.split(' ')
        y = y_str.split(' ')
        sm = SequenceMatcher(None, x, y)
        repl_str = []
        del_str = []
        ins_str = []
        # SequenceMatcher.get_opcodes() -  https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher.get_opcodes
        for opcodes in sm.get_opcodes():
            if opcodes[0] == 'equal':
                continue
            elif opcodes[0] == 'replace':
                tmp_str = ''
                for st in x[opcodes[1]:opcodes[2]]:
                    tmp_str += '- ' + st + '\n'
                for st in y[opcodes[3]:opcodes[4]]:
                    tmp_str += '+ ' + st + '\n'
                repl_str.append(tmp_str[:-1])
            elif opcodes[0] == 'insert':
                tmp_str = ''
                for st in y[opcodes[3]:opcodes[4]]:
                    tmp_str += '+ ' + st + '\n'
                ins_str.append(tmp_str[:-1])
            elif opcodes[0] == 'delete':
                tmp_str = ''
                for st in x[opcodes[1]:opcodes[2]]:
                    tmp_str += '- ' + st + '\n'
                del_str.append(tmp_str[:-1])
        insert[i] = ins_str
        delete[i] = del_str
        replace[i] = repl_str
        if insert[i] == [] and delete[i] == [] and replace[i] == []:
            print('here', i)
            nan_count += 1
            pass
    insert = np.array(insert)
    delete = np.array(delete)
    replace = np.array(replace)
    diffset = []
    print("nan_count", nan_count)
    # Create Final Repair class by combining insert, delete and replace
    for i in range(len(replace)):
        tmp_str = ''
        err_s = str(errset[i])
        if err_s == "nan":
            err_s = ""
        tmp_str += err_s + '\n'
        for repl in replace[i]:
            tmp_str += repl + '\n'
        for dlt in delete[i]:
            tmp_str += dlt + '\n'
        for ins in insert[i]:
            tmp_str += ins + '\n'
        # if len(tmp_str) <= 1:
        #     print("here")
        #     pass
        diffset.append(tmp_str[:-1])
    diffset = np.array(diffset)
    return diffset, insert, delete, replace


def train_logreg(X, Y):
    logreg = LogisticRegression()
    logreg.fit(X, Y)
    return logreg


def train_insdel(X, Y):
    model = Sequential()
    model.add(Dense(128, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(128, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(Y.shape[1], activation='softmax'))
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(X, Y, epochs=10, batch_size=10, verbose=False)
    return model


def train_non_lin_classifier(X, Y):
    model = Sequential()
    model.add(Dense(128, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(128, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer='Adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, Y, epochs=10, batch_size=10, verbose=False)
    return model


def train_repl_class(X, Y):
    model = Sequential()
    model.add(Dense(256, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(256, input_shape=(X.shape[1],), activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(Y.shape[1], activation='softmax'))
    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.fit(X, Y, epochs=15, batch_size=10, verbose=False)
    return model


# Train (no. of classes) OVR models to predict repair profiles vector
def train_multiple_rankers(oh_labels, int_labels, bigram, edit_pos):
    models = [0] * oh_labels.shape[1]
    accuracies = []
    glb_cnt = 0
    test_cnt = 0
    for i in range(oh_labels.shape[1]):
        models[i] = OneVsRestClassifier(DecisionTreeClassifier())
        train_X = bigram[np.where(int_labels == i)]
        train_Y = edit_pos[np.where(int_labels == i)]
        models[i].fit(train_X, train_Y)
    #        print(i)
    return models, accuracies


print("Preprocessing...")
tic = timer()

diffset, insert, delete, replace = get_repair_classes(data)

encoder = LabelEncoder()
labels = encoder.fit_transform(diffset)

one_hot_labels = keras.utils.to_categorical(labels)

counts = one_hot_labels.sum(axis=0)

# Remove classes with just 1 training example
del_items = []
for i in range(len(counts)):
    if counts[i] < 2:
        del_items.append(i)

del_indexes = one_hot_labels[:, del_items].any(1)
justOneOccurrence = np.sum(del_indexes)
# all_class = dict(Counter(diffset))
# new_all_class = dict()
# for key, value in all_class.items():
#     nKey = key.replace("\n", " <> ")
#     new_all_class[nKey] = value
# all_class = new_all_class
# all_class = pd.DataFrame(list(all_class.items()), columns=['class', 'frequency'])
# all_class.to_csv(CF.pathOut + "/all_classes.csv")

print("diffset before", len(diffset))
diffset = diffset[~del_indexes]

print("Number of classes having just 1 occurrence {}".format(justOneOccurrence))
print("diffset length : ", len(diffset))

#################################################################
if wo_err_id:
    diffset_wo_err_ids = []
    err_ids = []
    for i in range(len(diffset)):
        tokens = "\n".join(diffset[i].split("\n")[1:])
        err_ids.append(diffset[i].split("\n")[0])
        diffset_wo_err_ids.append(tokens)

    print("diffset_wo_err_id_len", len(diffset_wo_err_ids))
    print("err_ids_len", len(err_ids))
    # print("\nno of classes " + str(len(set(diffset_wo_err_ids))))
    diffset = np.array(diffset_wo_err_ids)
    # print("\ndiffset shape "  +str(diffset.shape))

#############################################################
print("no of classes ", len(set(diffset)))
new_encoder = LabelEncoder()
new_int_labels = new_encoder.fit_transform(diffset)

repair_class_dict = dict()
for i, cls in enumerate(sorted(new_encoder.classes_)):
    cls = cls.replace("\n", " \/ ")
    repair_class_dict[i] = cls



# repair_class_counts = dict()
# for cls in diffset:
#     cls = cls.replace("\n", " \/ ")
#     repair_class_counts[cls] = repair_class_counts.get(cls, 0) + 1
#
# repair_class_counts = {k: v for k, v in sorted(repair_class_counts.items())}
#
# repair_class_counts = pd.DataFrame(list(repair_class_counts.items()), columns=['repair_class', 'freq'])
# repair_class_counts.to_csv("../data/repair_classes_count.csv", index=False)


new_labels = keras.utils.to_categorical(new_int_labels)

if inferTypes:
    src_abs_lines = np.array(data['sourceLineTypeAbs'])
    tgt_abs_lines = np.array(data['targetLineTypeAbs'])

else:
    src_abs_lines = np.array(data['sourceLineAbs'])
    tgt_abs_lines = np.array(data['targetLineAbs'])

# src_lines = np.array(data['sourceLineText'])
# tgt_lines = np.array(data['targetLineText'])
# src_lines = src_lines[~del_indexes]
# tgt_lines = tgt_lines[~del_indexes]
src_abs_lines = src_abs_lines[~del_indexes]
tgt_abs_lines = tgt_abs_lines[~del_indexes]

# repair_class_dict_tmp = dict()
# for i, cls in enumerate(diffset):
#     cls = cls.replace("\n", " \/ ")
#     tmp_list = repair_class_dict_tmp.get(cls,[])
#     if not tmp_list:
#         tmp_list.append([src_abs_lines[i]])
#         tmp_list.append([tgt_abs_lines[i]])
#         tmp_list.append([src_lines[i]])
#         tmp_list.append([tgt_lines[i]])
#     else:
#         tmp_list[0].append(src_abs_lines[i])
#         tmp_list[1].append(tgt_abs_lines[i])
#         tmp_list[2].append(src_lines[i])
#         tmp_list[3].append(tgt_lines[i])
#     repair_class_dict_tmp[cls] = tmp_list
#
# with open("../tmp/repair_class_dump", 'wb') as file:
#     pickle.dump(repair_class_dict_tmp, file)
#
# exit()
insert = insert[~del_indexes]
delete = delete[~del_indexes]
replace = replace[~del_indexes]

errset = errset[~del_indexes]

feature_vector = get_feature_vector(src_abs_lines, errset)

tkn = keras.preprocessing.text.Tokenizer(filters='')
tkn.fit_on_texts(feature_vector)
encoded_vec = tkn.texts_to_matrix(feature_vector)
print("encdoed_vec shape", encoded_vec.shape)
print("Preprocessing Done.")
print("Training Repair Class Classifiers...")

# def train_lin_classifier(X, Y):
#     lin_svm = LinearSVC()
#     lin_svm.fit(X, Y)
#     return lin_svm


# replace vs no replace labels
coarse_one = []
for i in range(len(src_abs_lines)):
    if replace[i] != [] and insert[i] == [] and delete[i] == []:
        coarse_one.append(1)
    else:
        coarse_one.append(0)

coarse_one = np.array(coarse_one)

repl_or_not = train_non_lin_classifier(encoded_vec, coarse_one)

# def predict_repl(repl_or_not, X):
#     p = repl_or_not.predict(X.reshape(1, X.shape[0]))[0][0]
#     if p > 0.5:
#         return 1
#     return 0


# insert vs delete vs misc classes
noRepl_ind = np.where(coarse_one == 0)
noRepl_diffset = diffset[noRepl_ind]
noRepl_replace = replace[noRepl_ind]
noRepl_delete = delete[noRepl_ind]
noRepl_insert = insert[noRepl_ind]
noRepl_encoded_vec = encoded_vec[noRepl_ind]

# lines only needing insert (1) , only delete (2) and misc (0)
coarse_two = []
for i in range(len(noRepl_encoded_vec)):
    if noRepl_replace[i] == [] and noRepl_insert[i] != [] and noRepl_delete[i] == []:
        coarse_two.append(1)
    elif noRepl_replace[i] == [] and noRepl_insert[i] == [] and noRepl_delete[i] != []:
        coarse_two.append(2)
    else:
        coarse_two.append(0)
coarse_two = np.array(coarse_two)

ctwo_oh = keras.utils.to_categorical(coarse_two)

ins_del_model = train_insdel(noRepl_encoded_vec, ctwo_oh)

# def predict_insdel(ins_del_model, X):
#     p = ins_del_model.predict(X.reshape(1, X.shape[0]))[0]
#     return np.argmax(p)


repl_ind = np.where(coarse_one == 1)
repl_diffset = diffset[repl_ind]
repl_encoded_vec = encoded_vec[repl_ind]

repl_encoder = LabelEncoder()
repl_int_labels = repl_encoder.fit_transform(repl_diffset)
repl_oh_labels = keras.utils.to_categorical(repl_int_labels)
print("repl_oh_shape", repl_oh_labels.shape)

repl_class_model = train_repl_class(repl_encoded_vec, repl_oh_labels)

# def predict_repl_class(X):
#     p = qwe.predict(X.reshape(1, X.shape[0]))[0]
#     return np.argmax(p)


# Train prototype Classifiers
k_c = 25  # Max number of examples per cluster
repl_clusters = [0] * repl_oh_labels.shape[1]
for i in range(repl_oh_labels.shape[1]):
    train_X = repl_encoded_vec[np.where(repl_int_labels == i)]
    repl_clusters[i] = KMeans(math.ceil(train_X.shape[0] / k_c))
    repl_clusters[i].fit(train_X)

ins_ind = np.where(coarse_two == 1)
ins_diffset = noRepl_diffset[ins_ind]
ins_encoded_vec = noRepl_encoded_vec[ins_ind]

ins_encoder = LabelEncoder()
ins_int_labels = ins_encoder.fit_transform(ins_diffset)
ins_oh_labels = keras.utils.to_categorical(ins_int_labels)
print("ins_oh_shape", ins_oh_labels.shape)

ins_class_model = train_logreg(ins_encoded_vec, ins_int_labels)

ins_clusters = [0] * ins_oh_labels.shape[1]
for i in range(ins_oh_labels.shape[1]):
    train_X = ins_encoded_vec[np.where(ins_int_labels == 1)]
    ins_clusters[i] = KMeans(math.ceil(train_X.shape[0] / k_c))
    ins_clusters[i].fit(train_X)

del_ind = np.where(coarse_two == 2)
del_diffset = noRepl_diffset[del_ind]
del_encoded_vec = noRepl_encoded_vec[del_ind]

del_encoder = LabelEncoder()
del_int_labels = del_encoder.fit_transform(del_diffset)
del_oh_labels = keras.utils.to_categorical(del_int_labels)
print("del_oh_shape", del_oh_labels.shape)

del_class_model = train_logreg(del_encoded_vec, del_int_labels)

del_clusters = [0] * del_oh_labels.shape[1]
for i in range(del_oh_labels.shape[1]):
    train_X = del_encoded_vec[np.where(del_int_labels == i)]
    del_clusters[i] = KMeans(math.ceil(train_X.shape[0] / k_c))
    del_clusters[i].fit(train_X)

rest_ind = np.where(coarse_two == 0)
rest_diffset = noRepl_diffset[rest_ind]
rest_encoded_vec = noRepl_encoded_vec[rest_ind]

rest_encoder = LabelEncoder()
rest_int_labels = rest_encoder.fit_transform(rest_diffset)
rest_oh_labels = keras.utils.to_categorical(rest_int_labels)
print("rest_oh_shape", rest_oh_labels.shape)

repair_class_counts = dict()
for i, cls in enumerate(rest_encoder.classes_):
    cls = cls.replace("\n", " \/ ")
    # repair_class_counts[cls] = repair_class_counts.get(cls, 0) + 1
    repair_class_counts[i] = cls

# repair_class_counts = {k: v for k, v in sorted(repair_class_counts.items())}

repair_class_counts = pd.DataFrame(list(repair_class_counts.items()), columns=['id', 'rest_class'])
repair_class_counts.to_csv("../data/rest_classes.csv", index=False)

rest_class_model = train_logreg(rest_encoded_vec, rest_int_labels)

rest_clusters = [0] * rest_oh_labels.shape[1]
for i in range(rest_oh_labels.shape[1]):
    train_X = rest_encoded_vec[np.where(rest_int_labels == i)]
    rest_clusters[i] = KMeans(math.ceil(train_X.shape[0] / k_c))
    rest_clusters[i].fit(train_X)

print("Repair Class Classification Training Done.")
print("Training OvA Classifiers...")
src_edits = []  # Find which tokens need edits
for i, line in enumerate(src_abs_lines):
    tmp_line_str = str(line)
    if tmp_line_str == "nan":
        tmp_line_str = ""
    line = tmp_line_str.split(' ')
    tmp_edit = [0] * len(line)
    tmp_tgt_abs_line = str(tgt_abs_lines[i])
    if tmp_tgt_abs_line == "nan":
        tmp_tgt_abs_line = ""
    sm = SequenceMatcher(None, line, tmp_tgt_abs_line.split(' '))
    for opcodes in sm.get_opcodes():
        if opcodes[0] != 'equal':
            if opcodes[0] == 'insert':
                if opcodes[1] == len(line):
                    tmp_edit[opcodes[1] - 1] = 1
                else:
                    tmp_edit[opcodes[1]] = 1
            else:
                for j in range(opcodes[1], opcodes[2]):
                    tmp_edit[j] = 1
    src_edits.append(tmp_edit)

src_bigram = []
edit_bigram = []
# Get which bigrams need edit from tokens
for i in range(len(src_abs_lines)):
    tmp_lst = []
    edit_lst = []
    tmp_line_str = str(src_abs_lines[i])
    if tmp_line_str == "nan":
        tmp_line_str = ""
    tmp_line = tmp_line_str.split(' ')
    for ind in range(len(tmp_line) - 1):
        if src_edits[i][ind] == 1 or src_edits[i][ind + 1] == 1:
            edit_lst.append(1)
        else:
            edit_lst.append(0)
        tmp_str = ''
        tmp_str += tmp_line[ind] + ' ' + tmp_line[ind + 1]
        tmp_lst.append(tmp_str)
    src_bigram.append(tmp_lst)
    edit_bigram.append(edit_lst)
src_bigram = np.array(src_bigram)
edit_bigram = np.array(edit_bigram)

edit_tkn = keras.preprocessing.text.Tokenizer(filters='')

edit_tkn.fit_on_texts(src_bigram)

encoded_bigram = edit_tkn.texts_to_matrix(src_bigram)

sparse_edit_pos = np.zeros((src_bigram.shape[0], len(edit_tkn.word_index) + 1))
# Generate repair profiles vector
for i in range(src_bigram.shape[0]):
    if src_bigram[i] == []:
        sparse_edit_pos[i][0] = 1
    for j in range(len(src_bigram[i])):
        if edit_bigram[i][j] == 1:
            idx = edit_tkn.word_index[src_bigram[i][j].lower()]
            sparse_edit_pos[i][idx] = 1

flat_rankers, flat_accuracies = train_multiple_rankers(new_labels, new_int_labels, encoded_bigram, sparse_edit_pos)

# save bigram to id mappings used while prediction
idx_to_bigram = {}
for key, val in edit_tkn.word_index.items():
    idx_to_bigram[val] = key
print("OvA Classification Done.")

toc = timer()
print("Time Taken: " + str(toc - tic))
model_dir = CF.models_dir + "/model"

if wo_err_id:
    model_dir += '_woerrid'

if more_data:
    model_dir += '_more_data'

if inferTypes:
    model_dir += '_type'

if new_data:
    model_dir += '_new_data'

if merged:
    model_dir += '_merged'

if not os.path.exists(model_dir):
    os.makedirs(model_dir)

repair_class_df = pd.DataFrame(list(repair_class_dict.items()), columns=['id', 'repair_class'])
repair_class_df.to_csv(model_dir + "/repair_classes.csv", index=False)

with open(model_dir + '/edit_pos_tokenizer', 'wb') as file:
    pickle.dump(edit_tkn, file)
with open(model_dir + '/feature_tokenizer', 'wb') as file:
    pickle.dump(tkn, file)
with open(model_dir + '/idx_to_bigram', 'wb') as file:
    pickle.dump(idx_to_bigram, file)
with open(model_dir + '/new_encoder', 'wb') as file:
    pickle.dump(new_encoder, file)
with open(model_dir + '/flat_rankers', 'wb') as file:
    pickle.dump(flat_rankers, file)
with open(model_dir + '/repl_or_not', 'wb') as file:
    pickle.dump(repl_or_not, file)
with open(model_dir + '/ins_del_model', 'wb') as file:
    pickle.dump(ins_del_model, file)
with open(model_dir + '/repl_class_model', 'wb') as file:
    pickle.dump(repl_class_model, file)
with open(model_dir + '/repl_encoder', 'wb') as file:
    pickle.dump(repl_encoder, file)
with open(model_dir + '/ins_class_model', 'wb') as file:
    pickle.dump(ins_class_model, file)
with open(model_dir + '/ins_encoder', 'wb') as file:
    pickle.dump(ins_encoder, file)
with open(model_dir + '/del_class_model', 'wb') as file:
    pickle.dump(del_class_model, file)
with open(model_dir + '/del_encoder', 'wb') as file:
    pickle.dump(del_encoder, file)
with open(model_dir + '/rest_class_model', 'wb') as file:
    pickle.dump(rest_class_model, file)
with open(model_dir + '/rest_encoder', 'wb') as file:
    pickle.dump(rest_encoder, file)
with open(model_dir + '/repl_clusters', 'wb') as file:
    pickle.dump(repl_clusters, file)
with open(model_dir + '/ins_clusters', 'wb') as file:
    pickle.dump(ins_clusters, file)
with open(model_dir + '/del_clusters', 'wb') as file:
    pickle.dump(del_clusters, file)
with open(model_dir + '/rest_clusters', 'wb') as file:
    pickle.dump(rest_clusters, file)
print("Model Saved.")
