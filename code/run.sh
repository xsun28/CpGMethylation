#!/bin/bash
containsElement () {
  while [[ $# -gt 0 ]]; do
        [[ "$1" == "$model" ]] && return 1
  shift
  done
  return 0
}

checkMethods () {
   r=1
   for model in ${models[@]}; do
        containsElement ${support_models[@]}
	if [[ $? -ne 1 ]]; then
        	r=$((r*$?))
		echo "wrong model input: $model"
	else 
		r=$((r*$?))
	fi 
   done
   return
}



PYTHONPATH=$(pwd)
rm ../logs/logging.conf
echo "Start to get all WGBS sites and transform from hg38 to hg19..."

WGBSSitesFile=../data/WGBS/all_wgbs_sites_winid.csv
if [[ !(-e "$WGBSSitesFile") ]]; then
	echo "WGBS sites file has been processed"
	#python prediction/WGBS_allsites_preprocess.py	
fi

echo "Got all WGBS hg19 sites"

read -p "Preprocess features for all WGBS sites? (Y/N) " allWGBSFeaturesProcess
if [[ "$allWGBSFeaturesProcess" == "Y" ]]; then
	read -p "For all WGBS sites or nearest 100k sites to TSS (True/False)" all
	read -p "Reset features process progress tracker? (True/False)" resetTracker
	if [[ "$all" == "True" ]]; then
		echo "All WGBS features have been processed"
		#python features_preprocess/WGBS_all_sites_feature_preprocess.py -a True -r $resetTracker
	elif [[ "$all" == "False" ]]; then
		echo "WGBS (TSS nearest 100k) features have been processed"
		#python features_preprocess/WGBS_all_sites_feature_preprocess.py -a False -r $resetTracker
	else
		echo "wrong input"
		exit
	fi
elif [[ "$allWGBSFeaturesProcess" == "N" ]]; then
	echo "Bypassing all WGBS features preprocess"
else
	echo "wrong input"
	exit
fi

traits=(amyloid cerad ceradaf tangles cogdec gpath braak)
sed -i "s/^dataset = .*/dataset = 'AD_CpG'/" common/commons.py
read -p "Preprocess features for AD 450k sites? (Y/N)" arrayFeatures
if [[ "${arrayFeatures}" == "Y" ]]; then
	read -p "Reset 450k features process progress tracker? (True/False)" reset450KTracker
	echo "Preprocess features for all 450K WGBS sites"
	#python features_preprocess/all450k_feature_preprocess.py -r $reset450KTracker
fi
for trait in ${traits[@]}; do
	read -p "Processing ${trait}? (Y/N)" processTrait
	if [[ ! ("$processTrait" == "Y") ]]; then
		continue
	fi
			
	echo "start processing $trait..."
	sed -i "s/\([[:space:]]\+type_name\) = .*/\1 = '$trait'/" common/commons.py
	read -p "Select training sites for ${trait}? (Y/N)" traitSelection
	if [[ "$traitSelection" == "Y" ]]; then
		echo "Start ${trait} training sites selection"
		#python sites_selection/AD_sites_selection.py
	fi
	
	read -p "Preprocess features for ${trait}? (Y/N)" traitFeatures
	if [[ "$traitFeatures" ==  "Y" ]]; then
		echo "Preprocess features for selected ${trait} training sites"
		#python features_preprocess/all_features_preprocess.py
	fi
		
	read -p "Features selection for ${trait}? (Y/N)" traitFeatureSelection
	if [[ "$traitFeatureSelection" == "Y" ]]; then
		echo "Selecting fetures for ${trait}"
		#python features_selection/feature_selection.py
	fi
		
	read -p "Hyperparameter tuning of models for ${trait}? (Y/N)" traitModelTuning
	if [[ "$traitModelTuning" == "Y" ]]; then
		echo "Tuning models for $trait"
		#python models/ModelSelectionTuning.py -u True
	fi
		
	read -p "WGBS sites and 450K sites methylation prediction for ${trait}? (Y/N)" traitPrediction
	if [[ "$traitPrediction" == "Y" ]]; then
		echo "Predict WGBS methylation for $trait"
		read -p "Retrain prediction model? (Y/N)" retrain
		if [[ "$retrain" == "Y" ]]; then
			retrain=True
		else
			retrain=False
		fi
		      support_models=(LogisticRegression xgbooster SVC RandomForestClassifier)
		r=0
		while [[ $r -ne 1 ]]; do

			read -p "Select models for prediction (${support_models[*]}): " models
			checkMethods
			if [[ $r -eq 1 ]]; then
 				break
			fi
		done
		#python prediction/WGBS_prediction.py -r $retrain -u True -m $models
	fi
done
read -p "Combine results for all AD traits? (Y/N)" combine
if [[ "$combine" == Y ]]; then
	echo "Combining results for All AD traits for top 500 methylated sites"
	#python prediction/WGBS_alltraits_prediction_AD -m $models
fi

