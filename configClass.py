#!/usr/bin/python

# File name: configClass.py
# Author: Heike Adel
# Date: January 2016

class Config:

  def __init__(self):
    filename2012queries = "ENTER_PATH_AND_FILENAME_2012_QUERIES"
    filename2013queries = "ENTER_PATH_AND_FILENAME_2013_QUERIES"
    filename2014queries = "ENTER_PATH_AND_FILENAME_2014_QUERIES"
    path2012assessments = "ENTER_PATH_TO_data_DIRECTORY_OF_2012_ASSESSMENTS" # e.g. /path/TAC_2012_KBP_English_Regular_Slot_Filling_Assessment_Results_V1.2/data
    path2013assessments = "ENTER_PATH_TO_data_DIRECTORY_OF_2013_ASSESSMENTS" # e.g. /path/LDC2013E91_TAC_2013_KBP_English_Regular_Slot_Filling_Evaluation_Assessment_Results_V1.1/data
    path2014assessments = "ENTER_PATH_TO_data_DIRECTORY_OF_2014_ASSESSMENTS" # e.g. /path/LDC2014E75_TAC_2014_KBP_English_Regular_Slot_Filling_Evaluation_Assessment_Results_V2.0/data
    self.pathCorpusOld = "ENTER_PATH_TO_data_DIRECTORY_OF_2010_SOURCECORPUS" # e.g. /path/TAC_2010_KBP_Source_Data/data
    self.pathCorpusNew = "ENTER_PATH_TO_data_DIRECTORY_OF_2013_SOURCECORPUS" # e.g. /path/LDC2013E45_TAC_2013_KBP_Source_Corpus_disc_2/data
    self.coreNLPpath = "ENTER_PATH_TO_CORENLP_DIRECTORY" # e.g. /path/stanford-corenlp-full-2014-01-04

    self.queryFiles = {'2012' : filename2012queries,
                '2013' : filename2013queries,
                '2014' : filename2014queries}
    self.assessmentFolders = {'2012' : path2012assessments,
                     '2013' : path2013assessments,
                     '2014' : path2014assessments}
    self.doc2pathfile = 'docIds2path.gz'
    self.aliasFile = 'aliasFile'
    self.synonymFile = 'synonyms'
    self.name2genderFile = 'name2gender.sorted'
    self.noAcronymFile = 'noAcronyms'
