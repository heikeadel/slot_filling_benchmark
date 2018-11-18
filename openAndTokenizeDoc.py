#!/usr/bin/python

# File name: openAndTokenizeDoc.py
# Author: Heike Adel
# Date: January 2016

import os
import os.path
import re
import sys
import gzip
from utilities import cleanWord
from configClass import Config

def getOriginalCharacter(char):
  result = char
  if char == '-LRB-':
    result = "("
  elif char == '-RRB-':
    result = ")"
  elif char == '-LCB-':
    result = "{"
  elif char == '-RCB-':
    result = "}"
  elif char == '-LSB-':
    result = "["
  elif char == '-RSB-':
    result = "]"
  elif char == '``':
    result = '"'
  elif char == "''":
    result = '"'
  elif char == '`':
    result = "'"
  result = re.sub(r'\&gt\;', '>', result)
  result = re.sub(r'\&lt\;', '<', result)
  result = re.sub(r'\&amp\;', '&', result)
  return result

def openDoc(filename, docId):
  config = Config()
  if ".gz" in filename:
    if os.path.isfile(filename):
      f = gzip.open(filename, 'r')
    else:
      filename = re.sub(r'\.gz$', '', filename)
      f = open(filename, 'r')
  else:
    f = open(filename, 'r')
  curPwd = os.getcwd()
  os.chdir(config.coreNLPpath)
  foundDoc = 0
  forTok = open(curPwd + '/lineForSent', 'w')
  for line in f:
    if docId in line:
      foundDoc = 1
    if foundDoc == 1:
      line = line.strip()
      forTok.write(line + "\n")
      if "</doc>" in line or "</DOC>" in line:
        break # at the end of document
  forTok.close()
  os.system("java -cp stanford-corenlp-3.3.1.jar:stanford-corenlp-3.3.1-models.jar:xom.jar:joda-time.jar:jollyday.jar:ejml-0.23.jar -Xmx3g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner -file " + curPwd + "/lineForSent -outputDirectory " + curPwd)
  afterTok = open(curPwd + '/lineForSent.xml', 'r')
  exampleTokenized = ""
  sentences = []
  curSentence = ""
  curOffsetSentence = ""
  offsets = []
  curNerSentence = ""
  curBegin = ""
  ners = []
  curWord = ""
  curOffset = ""
  curNer = ""
  offset2NormNer = {}
  for line in afterTok:
    line = line.strip()
    if "<sentence id" in line:
      if curSentence != "":
        sentences.append(curSentence.strip())
        offsets.append(curOffsetSentence.strip())
        ners.append(curNerSentence.strip())
      curSentence = ""
      curOffsetSentence = ""
      curNerSentence = ""
    elif "<token id" in line:
      curTokenId = re.sub(r'^\s*\<token id\=\"(\d+)\"\>\s*$', '\\1', line)
    elif "<word>" in line:
      newLine = re.sub(r'^\s*\<word\>(.*?)\<\/word\>\s*$', '\\1', line)
      curWord = getOriginalCharacter(newLine)
      curWord = re.sub(r'\xc2\xa0', ' ', curWord)
      #curWord = re.sub(r' ', '-_-', curWord)
    elif "<NER>" in line:
      curNer = re.sub(r'^\s*\<NER\>(.*?)\<\/NER\>\s*$', '\\1', line)
    elif "<NormalizedNER>" in line:
      normNer = re.sub(r'^\s*\<NormalizedNER\>(.*?)\<\/NormalizedNER\>\s*$', '\\1', line)
      normNer = re.sub(r'T(.*?)$', '', normNer)
      if not re.search(r'[^X\-\d]', normNer): # normalized date consists of only X, - and numbers
        if re.search(r'^\w{4}$', normNer):
          # append XX for month and day
          normNer += "-XX-XX"
        elif re.search(r'^\w{4}\-\w{2}$', normNer):
          # append XX for day
          normNer += "-XX"
        if re.search(r'^\w{4}\-\w{2}\-\w{2}$', normNer):
          offset2NormNer[curOffset] = normNer
    elif "<CharacterOffsetBegin>" in line:
      curOffset = re.sub(r'^\s*\<CharacterOffsetBegin\>(.*?)\<\/CharacterOffsetBegin\>\s*$', '\\1', line)
    elif "</token>" in line:
      if " " in curWord:
          curWordList = curWord.split()
          startOffset = curOffset
          lengthSoFar = 0
          for cw in curWordList:
            cw = re.sub(r'\xef\xbf\xbd', '', cw)
            if cw == '': # otherwise there will be more offsets than words in the sentence
              continue
            cw = cleanWord(cw)
            curSentence += cw + " "
            curNerSentence += curNer + " "
            curOffsetSentence += str(int(startOffset) + lengthSoFar) + " "
            lengthSoFar += len(cw) + 1
      else:
        curSentence += curWord + " "
        curNerSentence += curNer + " "
        curOffsetSentence += curOffset + " "
    elif "</sentences>" in line:
      if curSentence != "":
        sentences.append(curSentence.strip())
        ners.append(curNerSentence.strip())
        offsets.append(curOffsetSentence.strip())
      curSentence = ""
      curOffsetSentence = ""
      curNerSentence = ""
  afterTok.close()
  f.close()
  os.chdir(curPwd)
  return [sentences, offsets, ners, offset2NormNer]

