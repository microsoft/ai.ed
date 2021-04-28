import pandas as pd
import random
from difflib import SequenceMatcher
from Common import ConfigFile as CF
from Symbolic import ClusterError
from Symbolic.DataStructs import *
from math import ceil


wo_err_id = True


def error_args():
    print("Usage: python test_train_split.py dataset [split_ratio]")
    print("Ex: python test_train_split.py tracer_single [0.7]")
    sys.exit(1)


def get_repair_class_dict(df):
    repair_class_dict = dict()  # repair class dictionary { repair_class : list of indices }
    n = len(df)
    print("Pre-processing Data")
    # print progress in %
    freq = 15 # must be < 100
    intervals = int((n / 100) * freq)
    progress = freq
    char_cnt = 0
    # For each erroneous code
    for i, row in df.iterrows():
        srcID, targetID = str(row['id']) + '_source', str(row['id']) + '_target'
        srcText, targetText = str(row['sourceText']), str(row['targetText'])
        actLine = int(row['lineNums_Abs'])  # assuming singleL dataset

        # Parse the source/ erroneous code
        srcCodeObj, targetCodeObj = Code(srcText, codeID=srcID), Code(targetText, codeID=targetID)
        AllErrs = ClusterError.getAllErrs(CF.fname_newErrIDs)
        errSet = ClusterError.getErrSetStr(AllErrs, srcCodeObj)

        x = str(row['sourceLineAbs'])
        if x == 'nan':  x = ''
        x = x.split()
        y = str(row['targetLineAbs'])
        if y == 'nan':  y = ''
        y = y.split()
        sm = SequenceMatcher(None, x, y)
        repl_str = []
        del_str = []
        ins_str = []
        for opcodes in sm.get_opcodes():
            if opcodes[0] == 'equal':
                continue
            elif opcodes[0] == 'replace':
                tmp_str = ''
                for st in x[opcodes[1]: opcodes[2]]:
                    tmp_str += '- ' + st + '\n'
                for st in y[opcodes[3]: opcodes[4]]:
                    tmp_str += '+ ' + st + '\n'
                repl_str.append(tmp_str[: -1])
            elif opcodes[0] == 'insert':
                tmp_str = ''
                for st in y[opcodes[3]: opcodes[4]]:
                    tmp_str += '+ ' + st + '\n'
                ins_str.append(tmp_str[: -1])
            elif opcodes[0] == 'delete':
                tmp_str = ''
                for st in x[opcodes[1]: opcodes[2]]:
                    tmp_str += '- ' + st + '\n'
                del_str.append(tmp_str[: -1])
        tmp_str = ''

        if not wo_err_id:
            tmp_str += errSet + '\n'
        for repl in repl_str:
            tmp_str += repl + '\n'
        for dlt in del_str:
            tmp_str += dlt + '\n'
        for ins in ins_str:
            tmp_str += ins + '\n'
        repair_class = tmp_str[: -1]

        if repair_class_dict.get(repair_class, None) is None:
            repair_class_dict[repair_class] = []
        repair_class_dict[repair_class].append(i)

        # print progress in %
        if i != 0 and i % intervals == 0:
            if progress != 100:
                print(str(progress) + '%', end='...', flush=True)
                progress += freq
                char_cnt += 6
            if char_cnt % 60 == 0:
                print()
                char_cnt = 0
        if i == n-1 and i % intervals != 0:
            print(str(100) + "%")

    print("Done\n")
    return repair_class_dict


def gen_random_list_ids(lst_ind, split):
    n = len(lst_ind)
    rand_train_lst_ids = list()
    rand_test_lst_ids = list()
    if n == 1:
        if random.random() < 0.5:
            rand_test_lst_ids = lst_ind[0]
        else:
            rand_train_lst_ids = lst_ind[0]
    else:
        random.shuffle(lst_ind)
        split_id = ceil(n * split)
        rand_train_lst_ids = lst_ind[: split_id]
        rand_test_lst_ids = lst_ind[split_id:]
    return rand_train_lst_ids, rand_test_lst_ids


def split_data(file, split=0.8):

    df_data = pd.read_csv(file, encoding="ISO-8859-1")

    repair_class_dict = get_repair_class_dict(df_data)
    cols = list(df_data.columns)
    train_set = pd.DataFrame(columns=cols)
    test_set = pd.DataFrame(columns=cols)
    rc_dict_items = list(repair_class_dict.items())
    print("Generating Train/Test Set...")
    for repair_class, lst_ind in rc_dict_items:
        rand_train_lst_ids, rand_test_lst_ids = gen_random_list_ids(lst_ind, split)
        train_set = train_set.append(df_data.iloc[rand_train_lst_ids, :])
        test_set = test_set.append(df_data.iloc[rand_test_lst_ids, :])

    print("Done\n")
    return train_set, test_set


if __name__ == '__main__':
    print()
    split = 0.8 if len(sys.argv) < 3 else sys.argv[2]
    file_path = CF.fnameSingleL if len(sys.argv) < 2 else sys.argv[1]
    if file_path.split('.')[-1] == 'csv':
        train_df, test_df = split_data(file_path, split)
        curr_path, cf = os.path.split(file_path)
        print("Writing data to csv...", flush=True)
        train_df.to_csv(curr_path + os.sep + str(cf.split(".")[0]) + "_train.csv", index=False)
        test_df.to_csv(curr_path + os.sep + str(cf.split(".")[0]) + "_test.csv", index=False)
        print("Data written to " + os.path.abspath(curr_path) + os.sep)
    else:
        error_args()
