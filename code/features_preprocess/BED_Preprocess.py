#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 10:42:06 2018

@author: Xiaobo
"""

import pandas as pd
#import argparse
import sys
import os
from common import commons
home = commons.home
from features_preprocess import get_winid
import os
logger = commons.logger
###########################

class BED_Preprocessing(object):
    
    def __init__(self,h5s_file= home+'data/commons/ATAC_H5S',data_type='ATAC',sites_file = home+'data/commons/all_sites_winid.csv',additional_feature_file = home+'data/features/addtional_features'):
        self.h5s_file = h5s_file
        self.sites_file = sites_file
        self.additional_feature_file = additional_feature_file
        self.data_type = data_type
        logger.info('Processing features of bed files of type {} using binned features in {}, and merged with selected sites in {}, and saved in {}'.format(self.data_type,self.h5s_file,self.sites_file,self.additional_feature_file))
    
    def process(self):
        all_sites = pd.read_csv(self.sites_file)
        all_sites = get_winid.convert_chr_to_num(all_sites)
        counts_at_targets = pd.DataFrame(all_sites['winid']) #.sort_values(['winid'])
        if self.data_type == 'ATAC' or self.data_type == 'WGBS':
            with pd.HDFStore(self.h5s_file,'r') as h5s:
                for key in h5s.keys():
                    bed_counts = h5s[key]
                    counts_at_targets = pd.merge(counts_at_targets,bed_counts,on=['winid'],how='left')
                    counts_at_targets[key[1:]+'_'+self.data_type+'_counts'].fillna(0,inplace=True)
                    logger.info('merging select sites with {} {} is done'.format(self.data_type,key))
        elif self.data_type == 'RNASeq':
            for f in [f for f in os.listdir(self.h5s_file) if os.path.isfile(os.path.join(self.h5s_file, f))]:
                with pd.HDFStore(self.h5s_file+f,'r') as h5s:
                    logger.info("processing RNASeq feature of experiment {}".format(self.h5s_file+f))
                    for key in h5s.keys():
                        bed_counts = h5s[key]
                        counts_at_targets = pd.merge(counts_at_targets,bed_counts,on=['winid'],how='left')
                        counts_at_targets[key[1:]+'_'+self.data_type+'_counts'].fillna(0,inplace=True)
                        logger.info('processing RNASeq feature of sample {} is done'.format(key))
        else:
            logger.error('Unsupported data type: '+self.data_type)
            exit()
        with pd.HDFStore(self.additional_feature_file,'a') as h5s:
            h5s[self.data_type] = counts_at_targets
            logger.info('Merged {} features to selected sites are saved to {}'.format(self.data_type,self.additional_feature_file))
##############################   
#parser = argparse.ArgumentParser(description='ATAC processor')
#parser.add_argument('-i',required=True,help='input file directory path',dest='input',metavar='input dir',default='/home/ec2-user/extra_storage/CpG_EWAS/ENCODE_ATAC-seq/')
#parser.add_argument('-s',required=True,help='all sites with winid path',dest='sites',metavar='all sites winid',default='/home/ec2-user/all_sites_winid.csv')
#parser.add_argument('-w',required=True,help='window file',dest='win',metarvar='window file',default='/home/ec2-user/wins.txt')
#args = parser.parse_args()
#data_dir = args.input
#sites_file = args.sites
#win_path = args.win




    
