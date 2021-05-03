from copy import deepcopy

from ML.Globals import edit_tkn, tkn, idx_to_bigram, new_encoder, flat_rankers, repl_or_not, ins_del_model, \
    repl_class_model, repl_encoder, ins_class_model, ins_encoder, del_class_model, del_encoder, rest_class_model, \
    rest_encoder, repl_clusters, ins_clusters, del_clusters, rest_clusters, wo_err_id
# if compiler_features:
#     from srcT.Prediction.Globals import err_id_tkn, tfid_err_msg, tfid_type_err
from ML import Globals
from timeit import default_timer as timer

import keras
import math
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense, Dropout
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances


def predictAbs(srcAbsLine, errSet, trgtAbsLine, predAtK, err_msg, gold_repair_classes):
    '''Give the source abstract line (list of tokens/strings),
    errSet and predAtK,
returns the predicted abstract line (list of tokens/strings)'''

    src_line = ''
    for token in srcAbsLine:
        src_line += token + ' '
    src_line += '\n'
    start = timer()
    targetLines, corr_pred_rep, repair_classes = test(src_line, errSet, predAtK, err_msg, gold_repair_classes)
    Globals.predict += timer() - start
    if targetLines != []:
        repairedLines = targetLines
    else:
        repairedLines = [srcAbsLine]
    return repairedLines, corr_pred_rep, repair_classes


def test(src_line, errs, predAtK, err_msg, gold_repair_classes):
    '''Compare with ideal predicted target line'''
    tmp_bigram = create_bigram(src_line)

    enc_tmp_bigram = edit_tkn.texts_to_matrix(tmp_bigram)

    tmp_feat_vector = create_feat_vector(errs, src_line)

    enc_tmp_feat_vector = tkn.texts_to_matrix(tmp_feat_vector)

    ###############################################################
    # if compiler_features:
    #     type_err, err_msg = get_compiler_msg_repr(err_msg)
    #     enc_tmp_feat_vector = np.hstack((enc_tmp_feat_vector, type_err, err_msg))
    ###############################################################

    repl_p = repl_or_not.predict(enc_tmp_feat_vector)[0][0]

    noRepl = ins_del_model.predict(enc_tmp_feat_vector)[0]

    #####################################################
    # cmp_feature_vector = get_compiler_feature_vector(err_msg, errs)
    ############################################

    start = timer()

    repl_pred = repl_class_model.predict(enc_tmp_feat_vector)

    ins_pred = ins_class_model.predict_proba(enc_tmp_feat_vector)
    del_pred = del_class_model.predict_proba(enc_tmp_feat_vector)
    rest_pred = rest_class_model.predict_proba(enc_tmp_feat_vector)

    #####################################################################

    # repl_cmp_pred = repl_cmp_model.predict(cmp_feature_vector)
    # ins_cmp_pred = ins_cmp_model.predict(cmp_feature_vector)
    # del_cmp_pred = del_cmp_model.predict(cmp_feature_vector)
    # rest_cmp_pred = rest_cmp_model.predict(cmp_feature_vector)

    #####################################################################

    end = timer()

    # Globals.corr_cls += end - start

    # msk=get_repl_mask()
    # repl_dist=np.delete(repl_dist,msk,1)

    start = timer()

    repl_dist = get_dist(repl_clusters, enc_tmp_feat_vector)
    repl_pred = 0.2 * repl_dist + 0.8 * repl_pred # + 0.1 * repl_cmp_pred
    repl_pred = repl_pred * repl_p

    ins_dist = get_dist(ins_clusters, enc_tmp_feat_vector)
    msk = get_ins_mask()
    if msk.shape[0] > 0:
        ins_dist = np.delete(ins_dist, msk, 1)
    ins_pred = 0.2 * ins_dist + 0.8 * ins_pred #+ 0.1 * ins_cmp_pred
    ins_pred = ins_pred * (1 - repl_p) * noRepl[1]

    del_dist = get_dist(del_clusters, enc_tmp_feat_vector)
    msk = get_del_mask()
    if msk.shape[0] > 0:
        del_dist = np.delete(del_dist, msk, 1)
    del_pred = 0.2 * del_dist + 0.8 * del_pred # + 0.1 * del_cmp_pred
    del_pred = del_pred * (1 - repl_p) * noRepl[2]

    rest_dist = get_dist(rest_clusters, enc_tmp_feat_vector)
    msk = get_rest_mask()
    if msk.shape[0] > 0:
        rest_dist = np.delete(rest_dist, msk, 1)
    rest_pred = 0.2 * rest_dist + 0.8 * rest_pred #+ 0.1 * rest_cmp_pred
    rest_pred = rest_pred * (1 - repl_p) * noRepl[0]

    rp = re = ins = de = 0

    sorted_repl_pred = sorted(repl_pred[0], reverse=True)
    sorted_ins_pred = sorted(ins_pred[0], reverse=True)
    sorted_del_pred = sorted(del_pred[0], reverse=True)
    sorted_rest_pred = sorted(rest_pred[0], reverse=True)

    end = timer()

    # Globals.rerank += end - start

    targetLines = []
    repair_classes = []
    corr_pred_rep = False

    for i1 in range(predAtK):
        if sorted_repl_pred[rp] >= sorted_del_pred[de] and sorted_repl_pred[rp] >= sorted_ins_pred[ins] and \
                sorted_repl_pred[rp] >= sorted_rest_pred[re]:
            repl_p = 1
            edit = np.where(repl_pred[0] == sorted_repl_pred[rp])
            rp += 1
        elif sorted_ins_pred[ins] >= sorted_del_pred[de] and sorted_ins_pred[ins] >= sorted_repl_pred[rp] and \
                sorted_ins_pred[ins] >= sorted_rest_pred[re]:
            repl_p = 0
            noRepl = 1
            edit = np.where(ins_pred[0] == sorted_ins_pred[ins])
            ins += 1
        elif sorted_del_pred[de] >= sorted_ins_pred[ins] and sorted_del_pred[de] >= sorted_repl_pred[rp] and \
                sorted_del_pred[de] >= sorted_rest_pred[re]:
            repl_p = 0
            noRepl = 2
            edit = np.where(del_pred[0] == sorted_del_pred[de])
            de += 1
        elif sorted_rest_pred[re] >= sorted_del_pred[de] and sorted_rest_pred[re] >= sorted_ins_pred[ins] and \
                sorted_rest_pred[re] >= sorted_repl_pred[rp]:
            repl_p = 0
            noRepl = 0
            edit = np.where(rest_pred[0] == sorted_rest_pred[re])
            re += 1

        start = timer()
        if repl_p == 1:
            what_to_edit = repl_encoder.inverse_transform(edit[0][:1])
        else:
            if noRepl == 1:
                what_to_edit = ins_encoder.inverse_transform(edit[0][:1])
            elif noRepl == 2:
                what_to_edit = del_encoder.inverse_transform(edit[0][:1])
            else:
                what_to_edit = rest_encoder.inverse_transform(edit[0][:1])
        # print(src_line, what_to_edit)
        edit = new_encoder.transform(what_to_edit)
        edit_pos = np.zeros(shape=enc_tmp_bigram.shape)
        ones = np.where(enc_tmp_bigram[0] == 1)
        for one in ones[0]:
            edit_pos[0][one] = flat_rankers[edit[0]].estimators_[one].predict(enc_tmp_bigram)
        # edit_pos=flat_rankers[edit[0]].predict(enc_tmp_bigram)

        end = timer()
        # Globals.bigram_rank += end - start
    ##############################################################################
        # tmp_diff = what_to_edit[0].split('\n')[1:]

        if what_to_edit[0] in gold_repair_classes:
            corr_pred_rep = True
        if wo_err_id:
            tmp_diff = what_to_edit[0].split('\n')  # [0].split('\n')[1:]
        else:
            tmp_diff = what_to_edit[0].split('\n')[1:]
        curr_repair_class = edit[0]
    ##############################################################################

        pred_bigrams = get_predicted_bigrams(edit_pos, idx_to_bigram)
        where_to_edit = get_predicted_edit_pos(pred_bigrams, tmp_bigram)

        start = timer()
        where_to_edit = sorted(where_to_edit)
        # print(where_to_edit)
        add = []
        dl = []
        for token in tmp_diff:
            if token.startswith('-'):
                dl.append(token[2:])
            elif token.startswith('+'):
                add.append(token[2:])

        if add == []:
            split_line = src_line.split(' ')
            where_to_edit = sorted(where_to_edit, reverse=True)
            mask = [0] * len(split_line)
            #####################################################################

            token_index_list = []
            line_set = set()
            applicable = True
            for tok in dl:
                indices_tmp = [i for i, x in enumerate(split_line) if x == tok]
                if len(indices_tmp) > 0:
                    token_index_list.append(indices_tmp)
                else:
                    applicable = False
                if len(indices_tmp) >= 6:
                    pass

            if not applicable:
                continue
            # number of arrays
            n = len(token_index_list)
            tot_count = 1
            for i in range(n):
                tot_count *= len(token_index_list[i])
            # print("tot count" , tot_count , tmp_diff)
            use_other = False
            if tot_count <= 30:
                use_other = True

            if use_other:
                # to keep track of next element
                # in each of the n arrays
                indices = [0 for i in range(n)]

                while (1):
                    # prcurrent combination
                    index_set = set()
                    flag = True
                    for i in range(n):
                        if token_index_list[i][indices[i]] in index_set:
                            flag = False
                            break
                        index_set.add(token_index_list[i][indices[i]])

                    if flag:
                        target_line = ''
                        for l in range(len(split_line)):
                            if l not in index_set:
                                target_line += split_line[l] + ' '
                        target_line = target_line[:-1]
                        if target_line not in line_set:
                            targetLines.append(target_line.split(' ')[:-1])
                            repair_classes.append(curr_repair_class)
                            line_set.add(target_line)

                    # find the rightmost array that has more
                    # elements left after the current element
                    # in that array
                    next = n - 1
                    while (next >= 0 and
                           (indices[next] + 1 >= len(token_index_list[next]))):
                        next -= 1

                    # no such array is found so no more
                    # combinations left
                    if (next < 0):
                        break

                    # if found move to next element in that
                    # array
                    indices[next] += 1

                    # for all arrays to the right of this
                    # array current index again points to
                    # first element
                    for i in range(next + 1, n):
                        indices[i] = 0

            #####################################################################
            else:
                print("Not using other")
                for k in range(len(dl)):
                    flg = 0
                    if len(split_line) == 1:
                        s = split_line[0].replace(dl[k], '')
                        if s == '':
                            mask[0] = 1
                    else:
                        for j in where_to_edit:
                            for l in range(len(split_line) - 1):
                                tmp_str = split_line[l] + ' ' + split_line[l + 1]
                                if tmp_str == tmp_bigram[0][j]:
                                    s = split_line[l].replace(dl[k], '')
                                    if s == '':
                                        mask[l] = 1
                                        flg = 1
                                        where_to_edit.remove(j)
                                    else:
                                        s = split_line[l + 1].replace(dl[k], '')
                                        if s == '':
                                            mask[l + 1] = 1
                                            flg = 1
                                            where_to_edit.remove(j)
                                    break
                            if flg == 1:
                                break
                target_line = ''
                for l in range(len(split_line)):
                    if mask[l] != 1:
                        target_line += split_line[l] + ' '
                target_line = target_line[:-1]
                targetLines.append(target_line.split(' ')[:-1])
                repair_classes.append(curr_repair_class)
        elif dl == []:
            target = []
            add_all = ''
            for x in add:
                add_all += x + ' '
            add_all = add_all[:-1]
            if tmp_bigram[0] == []:
                target_line = add_all + ' ' + src_line
                targetLines.append(target_line.split(' ')[:-1])
                repair_classes.append(curr_repair_class)
                target_line = src_line + ' ' + add_all
                targetLines.append(target_line.split(' ')[:-1])
                repair_classes.append(curr_repair_class)
            else:
                for j in where_to_edit:
                    if j == 0:
                        edited_bigram = add_all + ' ' + tmp_bigram[0][j]
                        targetLines.append(ins_bigram_to_line(tmp_bigram, edited_bigram, j).split(' ')[:-1])
                        repair_classes.append(curr_repair_class)
                    if j - 1 not in where_to_edit:
                        edited_bigram = tmp_bigram[0][j].split(' ')[0] + ' ' + add_all + ' ' + \
                                        tmp_bigram[0][j].split(' ')[1]
                        targetLines.append(ins_bigram_to_line(tmp_bigram, edited_bigram, j).split(' ')[:-1])
                        repair_classes.append(curr_repair_class)
                    edited_bigram = tmp_bigram[0][j] + ' ' + add_all
                    targetLines.append(ins_bigram_to_line(tmp_bigram, edited_bigram, j).split(' ')[:-1])
                    repair_classes.append(curr_repair_class)
        else:
            split_line = src_line.split(' ')
            target_line = ''
            # edit here or not
            mask = [0] * len(split_line)
            if len(add) == len(dl):
                token_index_list = []
                applicable = True
                line_set = set()
                for tok, add_tok in zip(dl,add):
                    indices_tmp = [i for i, x in enumerate(split_line) if x == tok]
                    if len(indices_tmp) > 0:
                        token_index_list.append(indices_tmp)
                    else:
                        applicable = False
                    if len(indices_tmp) >= 6:
                        pass

                if not applicable:
                    continue
                # number of arrays
                n = len(token_index_list)
                tot_count = 1
                for i in range(n):
                    tot_count *= len(token_index_list[i])
                # print("tot count" , tot_count , tmp_diff)
                use_other = False
                if tot_count <= 30:
                    use_other = True

                if use_other:
                    # to keep track of next element
                    # in each of the n arrays
                    indices = [0 for i in range(n)]

                    while (1):
                        # prcurrent combination
                        index_set = set()
                        flag = True
                        for i in range(n):
                            if token_index_list[i][indices[i]] in index_set:
                                flag = False
                                break
                            index_set.add(token_index_list[i][indices[i]])

                        if flag:
                            target_line = ''
                            index_set = sorted(list(index_set))

                            tmp_dl = deepcopy(dl)
                            tmp_add = deepcopy(add)
                            # for ind in index_set:
                            #     tok = split_line[ind]
                            #     index = tmp_dl.index(tok)
                            #     repl_list.append(tmp_add[index])
                            #     tmp_dl.pop(index)
                            #     tmp_add.pop(index)

                            for l in range(len(split_line)):
                                if l not in index_set:
                                    target_line += split_line[l] + ' '
                                else:
                                    tok = split_line[l]
                                    index = tmp_dl.index(tok)
                                    target_line += tmp_add[index] + ' '
                                    tmp_dl.pop(index)
                                    tmp_add.pop(index)

                            target_line = target_line[:-1]
                            if target_line not in line_set:
                                targetLines.append(target_line.split(' ')[:-1])
                                repair_classes.append(curr_repair_class)
                                line_set.add(target_line)

                        # find the rightmost array that has more
                        # elements left after the current element
                        # in that array
                        next = n - 1
                        while (next >= 0 and
                               (indices[next] + 1 >= len(token_index_list[next]))):
                            next -= 1

                        # no such array is found so no more
                        # combinations left
                        if (next < 0):
                            break

                        # if found move to next element in that
                        # array
                        indices[next] += 1

                        # for all arrays to the right of this
                        # array current index again points to
                        # first element
                        for i in range(next + 1, n):
                            indices[i] = 0
                else:
                    print("Not using other repl")
                    for x, y in zip(add, dl):
                        flg = 0
                        for j in where_to_edit:
                            for l in range(len(split_line) - 1):
                                tmp_str = split_line[l] + ' ' + split_line[l + 1]
                                if tmp_str == tmp_bigram[0][j] and mask[l] == 0 and mask[l + 1] == 0:
                                    s = split_line[l].replace(y, x)
                                    if s != split_line[l]:
                                        mask[l] = s
                                        flg = 1
                                        where_to_edit.remove(j)
                                    else:
                                        s = split_line[l + 1].replace(y, x)
                                        if s != split_line[l + 1]:
                                            mask[l + 1] = s
                                            flg = 1
                                            where_to_edit.remove(j)
                                    break
                            if flg == 1:
                                break
                    target_line = ''
                    if tmp_bigram[0] != []:
                        for l in range(len(split_line)):
                            if mask[l] != 0:
                                target_line += str(mask[l]) + ' '
                            else:
                                target_line += split_line[l] + ' '
                        target_line = target_line[:-1]
            else:
                add_all = ''
                for x in add:
                    add_all += x + ' '
                add_all = add_all[:-1]
                split_line = src_line.split(' ')
                for k in range(len(dl) - 1):
                    flg = 0
                    for j in where_to_edit:
                        for l in range(len(split_line) - 1):
                            tmp_str = split_line[l] + ' ' + split_line[l + 1]
                            if tmp_str == tmp_bigram[0][j]:
                                s = split_line[l].replace(dl[k], '')
                                if s == '':
                                    mask[l] = 1
                                    flg = 1
                                    where_to_edit.remove(j)
                                else:
                                    s = split_line[l + 1].replace(dl[k], '')
                                    if s == '':
                                        mask[l + 1] = 1
                                        flg = 1
                                        where_to_edit.remove(j)
                                break
                        if flg == 1:
                            break
                flg = 0
                for j in where_to_edit:
                    for l in range(len(split_line) - 1):
                        tmp_str = split_line[l] + ' ' + split_line[l + 1]
                        if tmp_str == tmp_bigram[0][j]:
                            s = split_line[l].replace(dl[-1], add_all)
                            if s != split_line[l] and mask[l] != 1:
                                mask[l] = s
                                flg = 1
                                where_to_edit.remove(j)
                            else:
                                s = split_line[l + 1].replace(dl[-1], add_all)
                                if s != split_line[l + 1]:
                                    mask[l + 1] = s
                                    flg = 1
                                    where_to_edit.remove(j)
                            break
                    if flg == 1:
                        break
                target_line = ''
                for l in range(len(split_line)):
                    if mask[l] != 0 and mask[l] != 1:
                        target_line += str(mask[l]) + ' '
                    elif mask[l] != 1:
                        target_line += split_line[l] + ' '
                target_line = target_line[:-1]
            # if target_line not in targetLines:
            targetLines.append(target_line.split(' ')[:-1])
            repair_classes.append(curr_repair_class)
            add_all = ''
            for x in add:
                add_all += x + ' '
            add_all = add_all[:-1]
            split_line = src_line.split(' ')
            mask = [0] * len(split_line)
            for k in range(len(dl)):
                flg = 0
                i = 0
                while i < len(where_to_edit):
                    for l in range(len(split_line) - 1):
                        tmp_str = split_line[l] + ' ' + split_line[l + 1]
                        if tmp_str == tmp_bigram[0][where_to_edit[i]]:
                            s = split_line[l].replace(dl[k], '')
                            if s == '':
                                mask[l] = 1
                                flg = 1
                            s = split_line[l + 1].replace(dl[k], '')
                            if s == '':
                                mask[l + 1] = 1
                                flg = 1
                            break
                    if flg == 1:
                        break
                    i += 1
            for j in where_to_edit:
                for l in range(len(split_line) - 1):
                    tmp_str = tmp_bigram[0][j]
                    if tmp_str == split_line[l] + ' ' + split_line[l + 1]:
                        if mask[l] != 1:
                            split_line[l] = split_line[l] + ' ' + add_all
                            targetLines.append(make_target_line(split_line, mask).split(' ')[:-1])
                            repair_classes.append(curr_repair_class)
                        if mask[l + 1] != 1:
                            split_line[l + 1] = split_line[l + 1] + ' ' + add_all
                            targetLines.append(make_target_line(split_line, mask).split(' ')[:-1])
                            repair_classes.append(curr_repair_class)
        end = timer()
        # Globals.fixer += end - start
    # print(targetLines)
    return targetLines, corr_pred_rep, repair_classes


def make_target_line(split_line, mask):
    target_line = ''
    for l in range(len(split_line)):
        if mask[l] == 0:
            target_line += split_line[l] + ' '
    target_line = target_line[:-1]
    return target_line


def create_bigram(src_line):
    tmp_bigram = []
    tmp_lst = []
    tmp_line = src_line.split(' ')
    for ind in range(len(tmp_line) - 1):
        tmp_str = ''
        tmp_str += tmp_line[ind] + ' ' + tmp_line[ind + 1]
        tmp_lst.append(tmp_str)
    tmp_bigram.append(tmp_lst)
    return tmp_bigram


def create_feat_vector(errs, src_line):
    tmp_feat_vector = []
    tmp_lst = []
    for err in errs.split(' '):
        tmp_lst.append(err.split(';')[0])
    tmp_line = src_line.split(' ')
    for abst in tmp_line:
        tmp_lst.append(abst)
    for ind in range(len(tmp_line) - 1):
        tmp_lst.append(tmp_line[ind] + ' ' + tmp_line[ind + 1])
    tmp_feat_vector.append(tmp_lst)
    return tmp_feat_vector


def get_predicted_bigrams(specific_prediction, idx_to_bigram):
    predicted_bigrams = []
    for x in np.where(specific_prediction[0] == 1)[0]:
        if idx_to_bigram.get(x) != None:
            predicted_bigrams.append(idx_to_bigram[x])
        else:
            predicted_bigrams.append(-1)
    return predicted_bigrams


def get_predicted_edit_pos(predicted_bigrams, act_bigram):
    pred_edit_pos = []
    for x in range(len(predicted_bigrams)):
        if predicted_bigrams[x] == -1:
            pred_edit_pos.append(-1)
            continue
        for y in range(len(act_bigram[0])):
            if predicted_bigrams[x] == act_bigram[0][y].lower():
                pred_edit_pos.append(y)
    return pred_edit_pos


def ins_bigram_to_line(tmp_bigram, edited_bigram, j):
    target_line = ''
    if j == 0:
        target_line += edited_bigram + ' '
    else:
        target_line += tmp_bigram[0][0] + ' '
    for x in range(1, len(tmp_bigram[0])):
        if x == j:
            target_line += edited_bigram.split(' ', maxsplit=1)[-1] + ' '
        else:
            target_line += tmp_bigram[0][x].split(' ', maxsplit=1)[-1] + ' '
    target_line = target_line[:-1]
    return target_line


# def filter_bigrams(tmp_diff, tmp_enc_src_bigram, idx_to_bigram):
#     idxs = []
#     for tkns in tmp_diff:
#         if tkns.startswith('-'):
#             for k in range(1, tmp_enc_src_bigram.shape[1]):
#                 if idx_to_bigram.get(k) != None:
#                     if tkns[2:].lower() in idx_to_bigram.get(k):
#                         if str(k) not in idxs:
#                             idxs.append(str(k))
#     tmp_tkn = keras.preprocessing.text.Tokenizer(filters='')
#     tmp_tkn.fit_on_texts(idxs)
#     filt_repl_enc_src_bigram = np.zeros((1, len(tmp_tkn.word_index) + 1))
#     for idx in idxs:
#         filt_repl_enc_src_bigram[0][tmp_tkn.word_index[idx]] = tmp_enc_src_bigram[0][int(idx)]
#     tmp_idx_to_bigram = get_idx_to_bigram(idx_to_bigram, tmp_tkn.word_index)
#     return tmp_idx_to_bigram, filt_repl_enc_src_bigram


def get_repl_mask():
    msk = []
    for i in range(len(repl_clusters)):
        if i not in repl_class_model.classes_:
            msk.append(i)
    msk = np.array(msk)
    return msk


def get_ins_mask():
    msk = []
    for i in range(len(ins_clusters)):
        if i not in ins_class_model.classes_:
            msk.append(i)
    msk = np.array(msk)

    return msk


def get_del_mask():
    msk = []
    for i in range(len(del_clusters)):
        if i not in del_class_model.classes_:
            msk.append(i)
    msk = np.array(msk)
    return msk


def get_rest_mask():
    msk = []
    for i in range(len(rest_clusters)):
        if i not in rest_class_model.classes_:
            msk.append(i)
    msk = np.array(msk)
    return msk


def get_dist(clusters, enc_tmp_feat_vector):
    clst = []
    for i in range(len(clusters)):
        if clusters[i].cluster_centers_.shape[0] == 1:
            clst.append(clusters[i].cluster_centers_[0])
        else:
            clst_dist = euclidean_distances(enc_tmp_feat_vector, clusters[i].cluster_centers_)[0]
            ind = np.where(clst_dist == min(clst_dist))[0][:1]
            clst.append(clusters[i].cluster_centers_[ind][0])
    clst = np.array(clst)
    dist = euclidean_distances(enc_tmp_feat_vector, clst)
    dist = np.exp((-1 / 2) * (dist ** 2))
    return dist


def predict_repl(repl_or_not, X):
    p = repl_or_not.predict(X)[0][0]
    if p > 0.5:
        return 1
    return 0


def predict_insdel(ins_del_model, X):
    p = ins_del_model.predict(X)[0]
    return np.argmax(p)

# def get_compiler_msg_repr(err_msg):
#     type_err_list = []
#     err_msg_list = []
#
#     for err in err_msg:
#         type_err_list.append(err.typeErr.lower())
#         err_msg_list.append(err.msg.lower())
#
#     # type_err = tfid_type_err.transform([" ".join(type_err_list)]).toarray()
#     # err_msg = tfid_err_msg.transform([" ".join(err_msg_list)]).toarray()
#     type_err = tfid_type_err.texts_to_matrix([" ".join(type_err_list)])
#     err_msg_ret = tfid_err_msg.texts_to_matrix([" ".join(err_msg_list)])
#     return type_err, err_msg_ret
