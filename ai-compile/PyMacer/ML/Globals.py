import os
import pickle
import tensorflow as tf
from Common import ConfigFile as CF

flags = {
    "merged" : 16,
    'nd' : 8,
    'weid': 4,  # w/o error id
    'md': 2,    # more data
    'ti': 1     # using type inference
}

# weid, md, ti
opt = int('10110', 2)

merged = opt & flags['merged']
new_data = opt & flags['nd']
wo_err_id = opt & flags['weid']
more_data = opt & flags['md']
inferTypes = opt & flags['ti']

slash = os.sep
dir_name = CF.models_dir + slash + 'model'
if wo_err_id:
    dir_name += '_woerrid'
if more_data:
    dir_name += '_more_data'
if inferTypes:
    dir_name += '_type'
if new_data:
    dir_name += '_new_data'
if merged:
    dir_name += '_merged'

with open(dir_name + '/edit_pos_tokenizer','rb') as file:
    edit_tkn = pickle.load(file)
with open(dir_name + '/feature_tokenizer','rb') as file:
    tkn = pickle.load(file)
with open(dir_name + '/idx_to_bigram','rb') as file:
    idx_to_bigram=pickle.load(file)
with open(dir_name + '/new_encoder','rb') as file:
    new_encoder=pickle.load(file)
with open(dir_name + '/flat_rankers','rb') as file:
    flat_rankers=pickle.load(file)
with open(dir_name + '/repl_encoder','rb') as file:
    repl_encoder=pickle.load(file)
with open(dir_name + '/ins_class_model','rb') as file:
    ins_class_model=pickle.load(file)
with open(dir_name + '/ins_encoder','rb') as file:
    ins_encoder=pickle.load(file)
with open(dir_name + '/del_class_model','rb') as file:
    del_class_model=pickle.load(file)
with open(dir_name + '/del_encoder','rb') as file:
    del_encoder=pickle.load(file)
with open(dir_name + '/rest_class_model','rb') as file:
    rest_class_model=pickle.load(file)
with open(dir_name + '/rest_encoder','rb') as file:
    rest_encoder=pickle.load(file)
with open(dir_name + '/repl_clusters','rb') as file:
    repl_clusters=pickle.load(file)
with open(dir_name + '/ins_clusters','rb') as file:
    ins_clusters=pickle.load(file)
with open(dir_name + '/del_clusters','rb') as file:
    del_clusters=pickle.load(file)
with open(dir_name + '/rest_clusters','rb') as file:
    rest_clusters=pickle.load(file)

# === Tf models ====

repl_or_not = tf.keras.models.load_model(dir_name + slash + 'repl_or_not')
ins_del_model = tf.keras.models.load_model(dir_name + slash + 'ins_del_model')
repl_class_model = tf.keras.models.load_model(dir_name + slash + 'repl_class_model')

# with open(dir_name + '/repl_or_not','rb') as file:
#     repl_or_not=pickle.load(file)
#     repl_or_not._make_predict_function()
# with open(dir_name + '/ins_del_model','rb') as file:
#     ins_del_model=pickle.load(file)
#     ins_del_model._make_predict_function()
# with open(dir_name + '/repl_class_model','rb') as file:
#     repl_class_model=pickle.load(file)
#     repl_class_model._make_predict_function()


# if compiler_features:
#     with open(dir_name + '/tfid_type_err', 'rb') as file:
#         tfid_type_err = pickle.load( file)
#     with open(dir_name + '/tfid_err_msg', 'rb') as file:
#         tfid_err_msg = pickle.load( file)
#     with open(dir_name + '/err_id_tkn', 'rb') as file:
#         err_id_tkn = pickle.load( file)

# with open(dir_name + '/repl_cmp_model', 'rb') as file:
#     repl_cmp_model = pickle.load( file)
# with open(dir_name + '/ins_cmp_model', 'rb') as file:
#     ins_cmp_model = pickle.load( file)
# with open(dir_name + '/del_cmp_model', 'rb') as file:
#     del_cmp_model = pickle.load( file)
# with open(dir_name + '/rest_cmp_model', 'rb') as file:
#     rest_cmp_model = pickle.load( file)


abstraction = 0
concretization = 0
compile_freq = 0
compile_time = 0
predict = 0
indent = 0
