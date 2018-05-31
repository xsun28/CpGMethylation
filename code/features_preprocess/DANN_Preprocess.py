#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 15:12:33 2018

@author: Xiaobo
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('/home/ec2-user/CpGPython/code/')
import get_winid
import pysam
################################################################

class DANN_Preprocess(object):
    
    def __init__(self,data_dir = '/home/ec2-user/extra_storage/CpG_EWAS/DANN/',
                 sites_file = '/home/ec2-user/CpGPython/data/all_sites_winid.csv',
                 additional_feature_file = '/home/ec2-user/CpGPython/data/features/addtional_features'):
        self.data_dir = data_dir
        self.sites_file = sites_file
        self.additional_feature_file = additional_feature_file
        
    def process(self):
        all_sites = pd.read_csv(self.sites_file)
        all_sites = get_winid.convert_chr_to_num(all_sites)
        dann_scores = []
        dann_file = self.data_dir+'DANN_whole_genome_SNVs.tsv.bgz'
        tabix = pysam.Tabixfile(dann_file)
        for site in all_sites.values:
            scores_one_site = []
            chrm = str(site[1])
            pos = int(site[2])
            left = pos
            right = pos-1
            while len(scores_one_site) == 0:
                left = left-1
                right = right+1
                for row in tabix.fetch(chrm,left,right,parser=pysam.asTuple()):
                    scores_one_site.extend([float(row[-1])])
            average_score = np.mean(scores_one_site)
            max_score = np.max(scores_one_site)
            dann_scores.extend([[chrm,pos,max_score,average_score]])
            print([chrm,pos,max_score,average_score])
        
        with pd.HDFStore(self.additional_feature_file,'a') as h5s:
            h5s['DANN'] = pd.DataFrame(dann_scores,columns=['chr','coordinate','DANN_max_score','DANN_avg_score']) 
               
        
#data_dir = '/Users/Xiaobo/Desktop/test.tsv'
#sites_file = '/Users/Xiaobo/Jobs/CpG/data/all_sites_winid.csv'
#win_path = '/home/ec2-user/CpGPython/data/wins.txt'

#---------------

#all_sites.sort_values(['chr','coordinate'],inplace=True)

#wins = get_winid.read_wins(win_path,chrs)
#-----------------

