#running script call as python ModelSelectionTuning.py -u True

import sys
import os
from common import commons
home = commons.home
logger = commons.logger
#sys.path.append('/home/ec2-user/anaconda3/lib/python3.6/site-packages')
import pandas as pd
import numpy as np
from sklearn.externals import joblib
from importlib import reload
from models.model_commons import *
import argparse

parser = argparse.ArgumentParser(description='Model Selection and Tuning for AD/Cd')
parser.add_argument('-u',required=False,default='True',help='upsampling data',dest='upsampling',metavar='True or False?')
parser.add_argument('-d',required=False,default='True',help='downsampling data',dest='downsampling',metavar='True or False?')
args = parser.parse_args()
up_sampling = (args.upsampling == 'True')
down_sampling = (args.downsampling == 'True')
logger.info(f"Training sites with positive samples upsampled: {up_sampling}, and test sites with negative samples downsampled:{down_sampling}")
down_sampling_marker = '' if down_sampling else 'imbalanced_' 

##features selecetd by traditional methods
dataset = commons.dataset
if dataset == 'AD_CpG':
    type_name = commons.type_name  ## amyloid, cerad, tangles
    with_cell_type = commons.with_cell_type ## with or without
    dataset = dataset+'/'+type_name+with_cell_type
logger.info(f"current model tuning trait is {dataset}")
if up_sampling:
    wtf_lo = 0.05 if dataset=="Cd" else 0.2
    wtf_hi = 0.1 if dataset=="Cd" else 0.3
    logger.info(f'upsampled sample weight factor range is from {wtf_lo} to {wtf_hi}')
else:
    wtf_lo = 1.0/3 if dataset=="Cd" else 0.4 
    wtf_hi = 0.5 if dataset=="Cd" else 0.45
    logger.info(f'not upsampled sample weight factor range is from {wtf_lo} to {wtf_hi}')

with pd.HDFStore(home+'data/'+dataset+'/selected_features','r') as h5s:
    train_x =h5s['train_x'] 
    train_label = h5s['train_label'] 
    test_x = h5s['test_x'] 
    test_label = h5s['test_label']
    sample_weights_train = h5s['sample_weights_train'] 
    sample_weights_test = h5s['sample_weights_test']
logger.info(f"max sample weight ratio in train dataset:{sample_weights_train.max()/sample_weights_train.min()}")
logger.info(f"max sample weight ratio in test dataset:{sample_weights_test.max()/sample_weights_test.min()}")

#10-fold test using the ensemble method
total_x = pd.concat([train_x,test_x],ignore_index=True)
total_label = pd.concat([train_label,test_label],ignore_index=True)
total_sample_weights = pd.concat([sample_weights_train,sample_weights_test],ignore_index=True)

methods_cv = ['LogisticRegression','SVC','xgbooster','RandomForestClassifier']
logger.info(f"models tested are {methods_cv}")
params_cv = get_hyperopt_params(methods_cv,wtf_lo=wtf_lo,wtf_hi=wtf_hi)
tenfold_crossval_scores,model_combine_scores_cv,model_scores_cv,best_params_cv,pred_probs_cv,predicts_cv,pred_probs_all_fold = cross_val_ensemble(total_x,total_label,total_sample_weights,methods_cv,params_cv,fold=10, up_sampling=up_sampling,down_sampling=down_sampling)
print('10-fold CV of ensemble method results:\n '+tenfold_crossval_scores.to_string())


joblib.dump(tenfold_crossval_scores,f'{home}data/{dataset}/{down_sampling_marker}tenfold_crossval_scores.pkl')
joblib.dump(model_combine_scores_cv,f'{home}data/{dataset}/{down_sampling_marker}model_combine_scores_cv.pkl')
joblib.dump(model_scores_cv,f'{home}data/{dataset}/{down_sampling_marker}model_scores_cv.pkl')
joblib.dump(best_params_cv,f'{home}data/{dataset}/{down_sampling_marker}best_params_cv.pkl')
joblib.dump(pred_probs_cv,f'{home}data/{dataset}/{down_sampling_marker}pred_probs_cv.pkl')
joblib.dump(predicts_cv,f'{home}data/{dataset}/{down_sampling_marker}predicts_cv.pkl')
joblib.dump(pred_probs_all_fold,f'{home}data/{dataset}/{down_sampling_marker}pred_probs_all_fold.pkl')


predicts_dtype = ['i8']*predicts_cv.shape[1]
probs_dtype = ['i8','f']+['f']*(pred_probs_cv.shape[1]-2)
for i,col in enumerate(predicts_cv.columns):
    predicts_cv[col] = predicts_cv[col].astype(predicts_dtype[i])
    pred_probs_cv[col] = pred_probs_cv[col].astype(probs_dtype[i])
    
avg_score_columns = ['ensemble']+methods_cv
avg_scores = {}
for method in avg_score_columns:
    avg_scores[method] = scores(predicts_cv['label'],predicts_cv[method],pred_probs_cv[method])
    
print("model average scores for "+dataset+": ")
print(avg_scores)

all_results,all_probs = methods_combination_results(methods_cv,pred_probs_all_fold,pd.Series(pred_probs_all_fold['label']))
all_probs = pd.DataFrame(all_probs)


print('model combination scores for '+dataset+': ')
print(all_results)

joblib.dump(all_results,f'{home}data/{dataset}/{down_sampling_marker}10fold_test_results.pkl')


plot_methods = ['LogisticRegression','SVC','xgbooster','RandomForestClassifier','LogisticRegression-xgbooster']

fig_name = f'{dataset.replace("/","_")}_{down_sampling_marker}10foldCV_allSitesPredProbs_'
plot_curves_cv(all_probs,pd.Series(pred_probs_all_fold['label']),methods=plot_methods,fig_name=fig_name,types='roc_curve')
plot_curves_cv(all_probs,pd.Series(pred_probs_all_fold['label']),methods=plot_methods,fig_name=fig_name,types='precision_recall_curve')

##plot all traits roc and pr curves of same method on a single plot
#if "AD_CpG" in dataset:
#    traits = ['amyloidwith','braakwith','ceradwith','ceradafwith','cogdecwith','gpathwith','tangleswith']
#    for method in all_probs.keys(): 
#        ploct_curves_all_traits(traits,method,types='roc_curve')
#        ploct_curves_all_traits(traits,method,types='precision_recall_curve')
        
print('model best hyperparameters for '+dataset+': ')
print(best_params_cv)

print("10-fold model combination for "+dataset+" scores: ")
print(model_combine_scores_cv)


 