import os
import platform

curr_path = os.path.realpath(__file__)
curr_path, cf = os.path.split(curr_path)

slash = os.sep
models_dir = curr_path + slash + '..' + slash + 'models'
dataPath = curr_path + slash + '..' + slash + 'data' + slash + 'Python CEs'
newDataPath = curr_path + slash + '..' + slash + 'data' + slash + 'dataset-2'

# '/trainGenerated.csv', '/trainnewSingleLine.csv', '/newSingleLine.csv', '/traingeneratedSingleLNoIndentError.csv'
# fnameSingleL_Train = dataPath + '/train.csv'
fnameSingleL_Train = dataPath + '/mergedTrain.csv'
# '/testGenerated.csv', '/testgeneratedSingleLNoIndentError.csv'
fnameSingleL_Test = dataPath + '/test.csv'
fnameSingleL_MoreData_Train = dataPath + '/more_data' + '/generatedtrain08_04_21.csv'

fname_newErrIDs = dataPath + '/errSet.csv'

fnameSingleL_Train_new = newDataPath + '/train.csv'
# '/testGenerated.csv', '/testgeneratedSingleLNoIndentError.csv'
fnameSingleL_Test_new = newDataPath + '/test.csv'
fnameSingleL_MoreData_Train_new = newDataPath + '/more_data' + '/generatedtrain08_04_21.csv'
# fnameSingleL = newDataPath + "/newSingleLine.csv"
fnameSingleL = dataPath + "/mergedNewSingleLine.csv"


fnameSingleL_Train_merged = dataPath + '/mergedNewSingleLine_train.csv'
# '/testGenerated.csv', '/testgeneratedSingleLNoIndentError.csv'
fnameSingleL_Test_merged = dataPath + '/mergedNewSingleLine_test.csv'
fnameSingleL_MoreData_Train_merged = dataPath + '/more_data' + '/generatedmergedNewSingleLine_train28_04_21_new.csv'
# fnameSingleL = newDataPath + "/newSingleLine.csv"
# fnameSingleL = dataPath + "/mergedNewSingleLine.csv"


pathOut = curr_path + slash + '..' + slash + 'output'
