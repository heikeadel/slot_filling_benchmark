#!/usr/bin/python

# File name: resourceManager.py
# Author: Heike Adel
# Date: January 2016

import re
import string
import sys
from configClass import Config
from glob import glob
import gzip

class Resources:

  ################# class methods ########################

  def readSynonyms(self):
    synonyms = {}
    f = open('synonyms', 'r')
    for line in f:
      line = line.strip()
      parts = line.split(' : ')
      for pInd, p in enumerate(parts):
        if not p in synonyms:
          synonyms[p] = []
        for qInd in range(len(parts)):
          if pInd != qInd:
            synonyms[p].append(parts[qInd])
    return synonyms

  def readAliasList(self):
    baseNameToAliasList = {}
    nameToBaseName = {}
    f = open(self.config.aliasFile, 'r')
    for line in f:
      if "ERROR" in line:
        continue
      line = line.strip()
      parts = line.split(' :: ')
      if len(parts) < 2:
        continue # no alias provided
      basename = parts[0]
      if basename in nameToBaseName:
        continue # do not overwrite already existing names
      nameToBaseName[basename] = basename
      tmpAliasList = [basename]
      for i in range(1, len(parts)):
        myName = parts[i]
        if myName in nameToBaseName:
          continue # do not overwrite
        tmpAliasList.append(myName)
        nameToBaseName[myName] = basename
      baseNameToAliasList[basename] = tmpAliasList
    f.close()
    return [baseNameToAliasList, nameToBaseName]

  def readDocId2Path(self):
    doc2path = {}
    f = gzip.open(self.config.doc2pathfile, 'r')
    for line in f:
      line = line.strip()
      parts = line.split()
      docid = parts[0]
      docpath = parts[1]
      if "PATH1" in docpath:
        docpath = re.sub(r'PATH1', self.config.pathCorpusOld, docpath)
      else:
        docpath = re.sub(r'PATH2', self.config.pathCorpusNew, docpath)
      doc2path[docid] = docpath
    f.close()
    return doc2path

  def testOffsets(self, fillerS, fillerE, proofS, proofE):
    fillerStart = int(fillerS)
    fillerEnd = int(fillerE)
    proofStart = int(proofS)
    proofEnd = int(proofE)
    if fillerStart + fillerEnd == 0:
      return 0
    if proofStart + proofEnd == 0:
      return 0
    if fillerStart < (proofStart - 5) or fillerStart > (proofEnd + 5): # some tolerance
      return 0
    if fillerEnd < (proofStart - 5) or fillerEnd > (proofEnd + 5):
      return 0
    return 1

  # reading assessment files:
  # 2012: format:
  # column 2: SF query ID + slot name
  # column 3: doc id
  # column 4: filler correctness
  # column 6: filler
  # column 8: filler offset
  # column 9: proof correctness
  # column 10: proof offset

  def readAssessment2012(self, key):
    assessments = []
    files = glob(self.config.assessmentFolders[key] + '/SF*')
    for singleFile in files:
      f = open(singleFile, 'r')
      for line in f:
        line = line.strip()
        parts = line.split('\t')
        fillerCorrectness = parts[3]
        proofCorrectness = parts[8]
        value = ""
        if fillerCorrectness == '1' or fillerCorrectness == '2':
          if proofCorrectness == '1':
            value = "+"
        elif fillerCorrectness == '-1' and proofCorrectness == '-1':
          value = "-"
        if value != "":
          queryId = parts[1].split(':')[0]
          slot = ":".join(parts[1].split(':')[1:])
          docId = parts[2]
          filler = parts[5]
          fillerOffset = parts[7]
          fillerStart = fillerOffset.split(':')[0]
          fillerEnd = fillerOffset.split(':')[1]
          proofOffset = parts[9]
          proofStart = proofOffset.split(':')[0]
          proofEnd = proofOffset.split(':')[1]
          name = self.id2name(queryId)
          if self.testOffsets(fillerStart, fillerEnd, proofStart, proofEnd) == 1:
            assessments.append([value, slot, name, filler, docId, fillerStart, fillerEnd, proofStart, proofEnd])
      f.close()
    return assessments

  # 2013: format:
  # column 2: SF query ID + slot name
  # column 3: doc id
  # column 4: filler
  # column 5: filler offset
  # column 6: name offset
  # column 7: proof offset
  # column 10: proof correctness
  # column 11: filler correctness (test: is it equal to column 8?)

  def readAssessment2013(self, key):
    assessments = []
    files = glob(self.config.assessmentFolders[key] + '/SF*')
    for singleFile in files:
      f = open(singleFile, 'r')
      for line in f:
        line = line.strip()
        parts = line.split('\t')
        fillerCorrectness = parts[10]
        proofCorrectness = parts[9]
        value = ""
        if fillerCorrectness == 'C' or fillerCorrectness == 'R':
          if proofCorrectness == 'C':
            value = "+"
        elif fillerCorrectness == 'W' and proofCorrectness == 'W':
          value = "-"
        if value != "":
          queryId = parts[1].split(':')[0]
          slot = ":".join(parts[1].split(':')[1:])
          docId = parts[2]
          filler = parts[3]
          fillerOffset = parts[4].split(',')[0]
          fillerStart = fillerOffset.split('-')[0]
          fillerEnd = fillerOffset.split('-')[-1]
          proofOffset = parts[6].split(',')[0]
          if proofOffset == "":
            continue
          proofStart = proofOffset.split('-')[0]
          proofEnd = proofOffset.split('-')[1]
          name = self.id2name(queryId)
          if self.testOffsets(fillerStart, fillerEnd, proofStart, proofEnd) == 1:
            assessments.append([value, slot, name, filler, docId, fillerStart, fillerEnd, proofStart, proofEnd])
      f.close()
    return assessments

  # 2014: format:
  # column 2: SF query ID + slot name
  # column 3: proof offset
  # column 4: filler
  # column 5: filler offset
  # column 6: filler correctness
  # column 7: proof correctness

  def readAssessment2014(self, key):
    assessments = []
    files = glob(self.config.assessmentFolders[key] + '/SF*')
    for singleFile in files:
      f = open(singleFile, 'r')
      for line in f:
        line = line.strip()
        parts = line.split('\t')
        fillerCorrectness = parts[5]
        proofCorrectness = parts[6]
        value = ""
        if fillerCorrectness == 'C' or fillerCorrectness == 'R':
          if proofCorrectness == 'C':
            value = "+"
        elif fillerCorrectness == 'W' and proofCorrectness == 'W':
          value = "-"
        if value != "":
          queryId = parts[1].split(':')[0]
          slot = ":".join(parts[1].split(':')[1:])
          filler = parts[3]
          fillerOffset = parts[4].split(',')[0]
          docId = fillerOffset.split(':')[0]
          fillerStart = fillerOffset.split(':')[1].split('-')[0]
          fillerEnd = fillerOffset.split(':')[1].split('-')[1]
          proofOffset = parts[2].split(',')[0]
          proofStart = proofOffset.split(':')[1].split('-')[0]
          proofEnd = proofOffset.split(':')[1].split('-')[1]
          name = self.id2name(queryId)
          if self.testOffsets(fillerStart, fillerEnd, proofStart, proofEnd) == 1:
            assessments.append([value, slot, name, filler, docId, fillerStart, fillerEnd, proofStart, proofEnd])
      f.close()
    return assessments

  def readQueries(self, filename):
    curQueryId = ""
    curName = ""
    id2name = {}
    f = open(filename)
    for line in f:
      line = line.strip()
      if "</query>" in line:
        id2name[curQueryId] = curName
      elif "<query id=" in line:
        # read new query id
        curQueryId = re.sub(r'^\s*\<query id\=\"(.*?)\"\>\s*$', '\\1', line)
      elif "<name>" in line:
        # read new name
        curName = re.sub(r'^\s*\<name\>(.*?)\<\/name\>\s*$', '\\1', line)
    return id2name

  def id2name(self, queryId):
    if queryId in self.id2nameList:
      return self.id2nameList[queryId]
    else:
      return queryId

  ################# constructor ###########################

  def __init__(self, yearList):

    self.config = Config()

    self.id2nameList = {}
    # read queries (to get id-to-name-mapping)
    for year in yearList:
      self.id2nameList.update(self.readQueries(self.config.queryFiles[year]))

    self.assessments = []
    # read assessment files
    for year in yearList:
      if '2012' in year:
        self.assessments.extend(self.readAssessment2012(year))
      elif '2013' in year:
        self.assessments.extend(self.readAssessment2013(year))
      elif '2014' in year:
        self.assessments.extend(self.readAssessment2014(year))
      else:
        sys.stderr.write("ERROR: skipping unknown year " + year)

    # read aliases for names:
    self.baseNameToAliasList, self.nameToBaseName = self.readAliasList()

    # read mapping docId to path
    self.doc2path = self.readDocId2Path()

    # read synonyms
    self.synonyms = self.readSynonyms()
