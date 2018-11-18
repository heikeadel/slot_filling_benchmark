#!/usr/bin/python

# File name: getData.py
# Author: Heike Adel
# Date: January 2016

import re
import string
from openAndTokenizeDoc import openDoc
from utilities import *
from resourceManager import Resources
from entitiesManager import Entities
from configClass import Config
import copy
import sys
from getOffsets import correctOffsets

###### main program ######

debug = 0 # debug 1: print ERROR and INFO messages, debug 2: print only INFO messages

# read assessment data and some external knowledge
config = Config()
resources = Resources(['2012', '2013', '2014'])
assessments = resources.assessments

doc2path = resources.doc2path
baseNameToAliasList = resources.baseNameToAliasList
nameToBaseName = resources.nameToBaseName
synonyms = resources.synonyms

# get alias information for entities
entities = Entities(assessments, baseNameToAliasList, nameToBaseName)
name2alias = entities.name2alias
name2gender = entities.name2gender

# suffixes which should be split in order to extract filler
toSplit = ["-based", "-month-old", "-year-old", "-born", "-area", "-educated", "-member", "-backed", "-mandate"]

# start: process assessments, one after one
for ind, item in enumerate(assessments):
  posNeg = item[0]
  slot = item[1]
  curName = item[2]
  filler = item[3]
  filler = re.sub(r'(\"\s*)+', '" ', filler)
  if curName == filler:
    # there is no reflexive relation
    continue
  docid = item[4]
  fillerStart = item[5]
  fillerEnd = item[6]

  if debug == 1 and not docid in doc2path:
    print "ERROR: could not open docid " + docid
    continue
  docpath = doc2path[docid]
  # open and tag document with NER information and offsets
  textPerLine, offsetsPerLine, nerPerLine, offset2NormNer = openDoc(docpath, docid)

  if len(textPerLine) == 0:
    # empty or not parseable document
    continue

  if len(textPerLine) != len(offsetsPerLine) or len(textPerLine) != len(nerPerLine) or len(offsetsPerLine) != len(nerPerLine):
    # tokenization did not work propably
    continue

  # adjust offsets: CoreNLP does not count spaces at the beginning of lines, but TAC does
  newOffsetsPerLine, newOffset2NormNer = correctOffsets(docid, docpath, textPerLine, offsetsPerLine, offset2NormNer)

  if debug == 1 and len(newOffsetsPerLine) == 0: # should not happen
    print "ERROR: " + docid + ": length offsets per line old: " + str(len(offsetsPerLine)) + ", and new: " + str(len(newOffsetsPerLine))
    continue

  offsetsPerLine = newOffsetsPerLine
  offset2NormNer = newOffset2NormNer

  sentence = ""
  ners = ""
  offsets = ""
  # extract sentence which contains filler
  # (since offsets could be inexact or too long, we don't relie on proofStart-proofEnd-offsets)  
  foundStartButNoEnd = 0
  foundIndexStart = -1
  foundIndexEnd = -1
  for index in range(len(offsetsPerLine)):
    curOffsets = offsetsPerLine[index]
    curWords = textPerLine[index]
    curNers = nerPerLine[index]
    firstOffset = curOffsets.split()[0]
    lastOffset = curOffsets.split()[-1]
    if foundStartButNoEnd == 1:
      foundIndexEnd = index # will be overwritten if it has not been the end
      if int(firstOffset) > int(fillerEnd):
        # filler end was somewhere in between the last sentence and this one
        break
      sentence += " " + curWords
      ners += " " + curNers
      offsets += " " + curOffsets
      if int(fillerEnd) <= int(lastOffset):
        break
    elif int(fillerStart) < int(firstOffset) or (int(fillerStart) >= int(firstOffset) and int(fillerStart) <= int(lastOffset)):
      foundIndexStart = index
      foundIndexEnd = index # will be overwritten if it has not been the end
      sentence = curWords
      ners = curNers
      offsets = curOffsets
      if int(fillerEnd) >= int(firstOffset) and int(fillerEnd) <= int(lastOffset):
        # extract just this one sentence
        break
      else:
        foundStartButNoEnd = 1

  # check whether sentence contains only HTML tags
  sentenceCleaned = cleanSentence(sentence).strip()
  if sentenceCleaned == "": # sentence contains only HTML tags
    if debug > 0:
      print "INFO: filler offsets: " + str(fillerStart) + " - " + str(fillerEnd)
      print "INFO: " + str(offsetsPerLine)
    if int(fillerStart) > int(offsetsPerLine[-1].split()[-1]): # filler is behind text according to offset: try last sentence
      sentence = textPerLine[-1]
      ners = nerPerLine[-1]
      offsets = offsetsPerLine[-1]
      sentenceCleaned = cleanSentence(sentence).strip()
      if sentenceCleaned == "" and len(textPerLine) > 1: # penultimate sentence if ultimate sentence consists of only HTML tags
        sentence = textPerLine[-2]
        ners = nerPerLine[-2]
        offsets = offsetsPerLine[-2]
        if debug > 0:
          print "INFO: choosing " + offsets
    else: # try sentence before or after this sentence (depending on which sentence is closer to filler offsets)
      curOffsets = offsets.split()
      if abs(int(fillerStart) - int(curOffsets[0])) < abs(int(fillerStart) - int(curOffsets[-1])):
        if foundIndexStart - 1 > 0:
          # sentence before that
          sentence = textPerLine[foundIndexStart - 1]
          ners = nerPerLine[foundIndexStart - 1]
          offsets = offsetsPerLine[foundIndexStart - 1]
          if debug > 0:
            print "INFO: choosing " + offsets
      else:
        if foundIndexEnd + 1 < len(textPerLine):
          # sentence after that
          sentence = textPerLine[foundIndexEnd + 1]
          ners = nerPerLine[foundIndexEnd + 1]
          offsets = offsetsPerLine[foundIndexEnd + 1]
          if debug > 0:
            print "INFO: choosing " + offsets

  if sentence == "": 
    # could not extract any sentence for filler offsets: offsets might be wrong
    continue

  fillerList = getFillerList(filler, synonyms)
  # split some known hyphen-seperated phrases
  fillerSplitted = filler.split()
  curIndex = 0
  if len(fillerSplitted) == 1: # remove pattern to get filler value
    word = fillerSplitted[curIndex]
    for pattern in toSplit:
      if pattern in word:
        wordBegin = re.sub(r'' + re.escape(pattern) + '$', '', word)
        fillerSplitted[curIndex] = wordBegin  # append only value of filler (and not the pattern)
        break
  # else: the filler contains additional information is, therefore, presumably evaluated as wrong although the context might fit to the slot - hence, it will be ignored to get clean data
  fillerJoined = " ".join(fillerSplitted)
  if not fillerJoined in fillerList:
    fillerList.append(fillerJoined)
  fillerListTok = tokenizeNames(fillerList, config.coreNLPpath)

  sentenceOrig = sentence

  sentenceList = sentence.split()
  offsetList = offsets.split()
  nerList = ners.split()
  if len(offsetList) != len(sentenceList) or len(offsetList) != len(nerList) or len(sentenceList) != len(nerList):
    continue
    # parsing did not work properly

  # preprocess extracted sentence:
  # split some known hyphen-seperated phrases
  curIndex = 0
  while curIndex < len(sentenceList):
    word = sentenceList[curIndex]
    for pattern in toSplit:
      if pattern in word:
        wordBegin = re.sub(r'' + re.escape(pattern) + '$', '', word)
        sentenceList[curIndex] = wordBegin
        sentenceList.insert(curIndex + 1, pattern)
        # calculate offset for pattern:
        patternOffset = int(offsetList[curIndex]) + len(wordBegin)
        offsetList.insert(curIndex + 1, str(patternOffset))
        nerList[curIndex] = "MISC"
        nerList.insert(curIndex + 1, "MISC")
        curIndex += 1
        break
    if word in ["African-American", "demographer-economist", "R-Wash.", "long-shot", "Wal-Mart", "R-OH", "R-Ohio", "Jewish-Arab"]:
      wordAsList = word.split('-')
      word1 = wordAsList[0]
      word2 = wordAsList[1]
      sentenceList[curIndex] = word1
      sentenceList.insert(curIndex + 1, '-')
      sentenceList.insert(curIndex + 2, word2)
      # calculate offset for second word:
      patternOffset = int(offsetList[curIndex]) + len(word1)
      offsetList.insert(curIndex + 1, str(patternOffset))
      offsetList.insert(curIndex + 2, str(patternOffset + 1))
      nerList.insert(curIndex + 1, nerList[curIndex])
      nerList.insert(curIndex + 2, nerList[curIndex])
      curIndex += 1
      break
    curIndex += 1
  sentence = " ".join(sentenceList)
  offsets = " ".join(offsetList)
  ners = " ".join(nerList)

  # process sentence:
  # 1. replace entity mentions with <name> tag
  # 2. replace filler with <filler> tag
  # the processing will mainly be done using the sentenceList and not the sentence string

  if not "<name>" in sentenceList:
    # replace name
    replacedName = 0
    listOfAlias = name2alias[curName]
    # look for aliases in sentence
    bestIndices = []
    for la in listOfAlias:
      if la in fillerListTok:
        continue
      hits = compareNames(la, sentence)
      updateBestIndices(bestIndices, hits)
    bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
    toDelete = []
    for bestStart, bestEnd in bestIndicesSorted:
      aliasInText = " ".join(sentenceList[bestStart : bestEnd])
      if re.search(r'^' + re.escape(aliasInText), filler):
        # alias is a prefix of filler: check whether occurrence is an occurrence of alias or of filler
        if re.search(r'^' + re.escape(filler), " ".join(sentenceList[bestStart :])):
          # filler occurrence: delete index from bestIndicesSorted        
          toDelete.append([bestStart, bestEnd])
    for d in toDelete:
      bestIndicesSorted.remove(d)
    for bestStart, bestEnd in bestIndicesSorted:
      # replace with <name>
      if nerTest(bestStart, bestEnd, nerList, sentenceList, slot) == 1:
        sentenceList[bestStart] = "<name>"
        for i in range(bestStart + 1, bestEnd):
          sentenceList.pop(bestStart + 1)
          if bestStart + 1 < len(nerList):
            nerList.pop(bestStart + 1)
          if bestStart + 1 < len(offsetList):
            offsetList.pop(bestStart + 1)
        # update strings as well
        sentence = " ".join(sentenceList)
        ners = " ".join(nerList)
        offsets = " ".join(offsetList)
        replacedName = 1
      else:
        if "org:" in slot and " ".join(sentenceList[bestStart : bestEnd]) == curName:
          # match full name for org without NER test
          sentenceList[bestStart] = "<name>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
            if bestStart + 1 < len(nerList):
              nerList.pop(bestStart + 1)
            if bestStart + 1 < len(offsetList):
              offsetList.pop(bestStart + 1)
          # update strings as well
          sentence = " ".join(sentenceList)
          ners = " ".join(nerList)
          offsets = " ".join(offsetList)
          replacedName = 1
    if replacedName == 0:
      listOfAliasExtended = []
      if "-" in curName.split()[-1]: # last name has a hyphen
        additionalAlias1 = curName.split()[-1].split('-')[0]
        additionalAlias2 = curName.split()[-1].split('-')[-1]
        listOfAliasExtended.append(additionalAlias1)
        listOfAliasExtended.append(additionalAlias2)
      bestStart = -1
      bestEnd = -1
      bestIndices = []
      for la in listOfAliasExtended:
        if la in fillerListTok:
          continue
        hits = compareNames(la, sentence)
        updateBestIndices(bestIndices, hits)
      bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
      toDelete = []
      for bestStart, bestEnd in bestIndicesSorted:
        aliasInText = " ".join(sentenceList[bestStart : bestEnd])
        if re.search(r'^' + re.escape(aliasInText), filler):
          # alias is a prefix of filler: check whether occurrence is an occurrence of alias or of filler
          if re.search(r'^' + re.escape(filler), " ".join(sentenceList[bestStart :])):
            # filler occurrence: delete index from bestIndicesSorted        
            toDelete.append([bestStart, bestEnd])
      for d in toDelete:
        bestIndicesSorted.remove(d)
      for bestStart, bestEnd in bestIndicesSorted:
        # replace with <name>
        if nerTest(bestStart, bestEnd, nerList, sentenceList, slot) == 1:
          sentenceList[bestStart] = "<name>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
            if bestStart + 1 < len(nerList):
              nerList.pop(bestStart + 1)
            if bestStart + 1 < len(offsetList):
              offsetList.pop(bestStart + 1)
          # update strings as well
          sentence = " ".join(sentenceList)
          ners = " ".join(nerList)
          offsets = " ".join(offsetList)
          replacedName = 1
        else:
          if "org:" in slot and " ".join(sentenceList[bestStart : bestEnd]) == curName:
            # match full name for org without NER test
            sentenceList[bestStart] = "<name>"
            for i in range(bestStart + 1, bestEnd):
              sentenceList.pop(bestStart + 1)
              if bestStart + 1 < len(nerList):
                nerList.pop(bestStart + 1)
              if bestStart + 1 < len(offsetList):
                offsetList.pop(bestStart + 1)
            # update strings as well
            sentence = " ".join(sentenceList)
            ners = " ".join(nerList)
            offsets = " ".join(offsetList)
            replacedName = 1

    if replacedName == 0:
      # match exact name also lower case
      hits = compareNames(string.lower(curName), string.lower(sentence))
      bestIndices = []
      if len(hits) > 0:
        updateBestIndices(bestIndices, hits)
      bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
      toDelete = []
      for bestStart, bestEnd in bestIndicesSorted:
        aliasInText = " ".join(sentenceList[bestStart : bestEnd])
        if re.search(r'^' + re.escape(aliasInText), filler):
          # alias is a prefix of filler: check whether occurrence is an occurrence of alias or of filler
          if re.search(r'^' + re.escape(filler), " ".join(sentenceList[bestStart :])):
            # filler occurrence: delete index from bestIndicesSorted        
            toDelete.append([bestStart, bestEnd])
      for d in toDelete:
        bestIndicesSorted.remove(d)
      for bestStart, bestEnd in bestIndicesSorted:
        # replace with <name>
        if nerTest(bestStart, bestEnd, nerList, sentenceList, slot) == 1:
          sentenceList[bestStart] = "<name>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
            if bestStart + 1 < len(nerList):
              nerList.pop(bestStart + 1)
            if bestStart + 1 < len(offsetList):
              offsetList.pop(bestStart + 1)
          # update strings as well
          sentence = " ".join(sentenceList)
          ners = " ".join(nerList)
          offsets = " ".join(offsetList)
          replacedName = 1

      if replacedName == 0:
        if "per:" in slot and not "alternate_names" in slot:
          # replace pronouns of the correct gender (for alternate_names we need both exact name and filler to get a useful context!)
          gender = name2gender[curName.split()[0]]
          if gender == "f":
            sentence = re.sub(r' [Ss]he ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Hh]er ', ' <name> ', " " + sentence + " ")
          else:
            sentence = re.sub(r' [Hh]e ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Hh]is ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Hh]im ', ' <name> ', " " + sentence + " ")
          if not "<name>" in sentence:
            # try 'I' pronoun
            sentence = re.sub(r' I ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Mm]e ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Mm]y ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Ww]e ', ' <name> ', " " + sentence + " ")
            sentence = re.sub(r' [Uu]s ', ' <name> ', " " + sentence + " ")
        elif "org:" in slot and not "alternate_names" in slot:
          # replace it
          sentence = re.sub(r' [Ii]ts ', ' <name> ', " " + sentence + " ")
          sentence = re.sub(r' [Ii]t ', ' <name> ', " " + sentence + " ")
        if "<name>" in sentence:
          sentence = sentence.strip()
          replacedName = 1
          # update lists as well
          sentenceList = sentence.split()

  if not "<name>" in sentence:
    if "-" in sentence or "/" in sentence:
      for la in listOfAlias:
        index = -1
        sign = ""
        la_escaped = re.escape(la)
        if re.search(r'' + la_escaped + '\/', sentence) or re.search(r'\/' + la_escaped, sentence): # (no fuzzy match here)
          sign = "/"
          index = getIndexOfName(sentence, la, sign)
        elif re.search(r'' + la_escaped + '\-', sentence) or re.search(r'\-' + la_escaped, sentence):
          sign = "-"
          index = getIndexOfName(sentence, la, sign)
        if index != -1:
          # split at sign
          sentencePart = sentenceList[index : index + len(la.split())]
          for spInd, sp in enumerate(sentencePart):
            if sign in sp:
              spNew = sp.split(sign)
              sentenceList[index + spInd] = spNew[0]
              for toInsert in range(1, len(spNew)):
                sentenceList.insert(index + spInd + toInsert, spNew[toInsert])
                nerList.insert(index + spInd + toInsert, nerList[index + spInd])
                patternOffset = int(offsetList[index + spInd]) + len(" ".join(sentencePart[:spInd]))
                offsetList.insert(index + spInd + toInsert, str(patternOffset))
          # replace with <name> tag
          for sIndex in range(0, len(sentenceList) - len(la.split()) + 1):
            sentencePart = sentenceList[sIndex : sIndex + len(la.split())]
            if " ".join(sentencePart) == la:
              sentenceList[sIndex] = "<name>"
              for toPopIndex in range(sIndex + 1, sIndex + len(la.split())):
                sentenceList.pop(sIndex + 1)
                nerList.pop(sIndex + 1)
                offsetList.pop(sIndex + 1)
          # update strings as well
          sentence = " ".join(sentenceList)
          ners = " ".join(nerList)
          offsets = " ".join(offsetList)
          break

  if debug == 1 and not "<name>" in sentence:
    print "ERROR: could not find name: " + str(item)
    continue

  sentenceAfterNameReplacement = sentence
  nersAfterNameReplacement = ners
  offsetsAfterNameReplacement = offsets

  if not "<filler>" in sentenceList:
    # replace filler
    if "date" in slot:
      # fuzzy date match
      offsetList = offsets.split()
      for wordIndex in range(len(sentenceList)):
        if offsetList[wordIndex] in offset2NormNer:
          normedNer = offset2NormNer[offsetList[wordIndex]]
          if re.search(r'[X0-9]+\-[X0-9]+\-[X0-9]+', normedNer):
            parts = normedNer.split('-')
            for fl in fillerListTok:
              fparts = fl.split('-')
              if len(parts) != len(fparts):
                continue
              noMatch = 0
              gotMatchNotX = 0
              for i in range(len(parts)):
                if parts[i] == fparts[i] or "X" in parts[i] or "X" in fparts[i]:
                  if not parts[i] in ["XX", "XXXX"] and not fparts[i] in ["XX", "XXXX"]:
                    if not parts[i] == fparts[i]:
                      # test whether there is a string like 191X and whether it matches the other string:
                      listOne = list(parts[i])
                      listTwo = list(fparts[i])
                      for j in range(len(listOne)):
                        if listOne[j] != listTwo[j] and (listOne[j] != 'X' and listTwo[j] != 'X'):
                          noMatch = 1
                          break
                    else:
                      gotMatchNotX = 1
                  # match
                  pass
                else:
                  noMatch = 1
                  break
              if noMatch == 0 and gotMatchNotX == 1:
                sentenceList[wordIndex] = '<filler>'
      # update string as well
      sentence = " ".join(sentenceList)
      if not "<filler>" in sentenceList:
        # lc string match
        bestIndices = []
        sentenceLc = string.lower(sentence)
        for fl in fillerListTok:
          flLc = string.lower(fl)
          hits = compareNames(flLc, sentenceLc)
          updateBestIndices(bestIndices, hits)
        bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
        for bestStart, bestEnd in bestIndicesSorted:
          # replace with <filler>
          sentenceList[bestStart] = "<filler>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
          # update string as well
          sentence = " ".join(sentenceList)
  
    elif "age" in slot and "-month-old" in sentence:
        indexPattern = sentenceList.index("-month-old")
        indexAge = indexPattern - 1
        year = month2year(sentenceList[indexAge])
        if year == filler:
          sentenceList[indexAge] = "<filler>"
        sentence = " ".join(sentenceList)

    else:
      bestIndices = []
      for fs in fillerListTok:
        hits = compareNames(fs, sentence)
        updateBestIndices(bestIndices, hits)
      bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
      for bestStart, bestEnd in bestIndicesSorted:
        # replace with <filler>
        sentenceList[bestStart] = "<filler>"
        for i in range(bestStart + 1, bestEnd):
          sentenceList.pop(bestStart + 1)
        # update string as well
        sentence = " ".join(sentenceList)

      if not "<filler>" in sentenceList:
        fillerFirstName = filler.split()[0]
        hits = compareNames(fillerFirstName, sentence)
        bestIndices = []
        updateBestIndices(bestIndices, hits)
        bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
        for bestStart, bestEnd in bestIndicesSorted:
          sentenceList[bestStart] = "<filler>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
          # update string as well
          sentence = " ".join(sentenceList)

      if not "<filler>" in sentenceList:
        # lc-match
        bestIndices = []
        sentenceLc = string.lower(sentence)
        for fl in fillerListTok:
          flLc = string.lower(fl)
          hits = compareNames(flLc, sentenceLc)
          updateBestIndices(bestIndices, hits)
        bestIndicesSorted = sorted(bestIndices, key=lambda x:x[0], reverse = True)
        for bestStart, bestEnd in bestIndicesSorted:
          # replace with <filler>
          sentenceList[bestStart] = "<filler>"
          for i in range(bestStart + 1, bestEnd):
            sentenceList.pop(bestStart + 1)
          # update string as well
          sentence = " ".join(sentenceList)

  if not "<filler>" in sentence:
    if "-" in sentence or "/" in sentence:
      for fl in fillerListTok:
        index = -1
        sign = ""
        fl_escaped = re.escape(fl)
        if re.search(r'' + fl_escaped + '\/', sentence) or re.search(r'\/' + fl_escaped, sentence): # (no fuzzy match here)
          sign = "/"
          index = getIndexOfName(sentence, fl, sign)
        elif re.search(r'' + fl_escaped + '\-', sentence) or re.search(r'\-' + fl_escaped, sentence):
          sign = "-"
          index = getIndexOfName(sentence, fl, sign)
        if index != -1:
          # split at sign
          sentencePart = sentenceList[index : index + len(fl.split())]
          for spInd, sp in enumerate(sentencePart):
            if sign in sp:
              spNew = sp.split(sign)
              sentenceList[index + spInd] = spNew[0]
              for toInsert in range(1, len(spNew)):
                sentenceList.insert(index + spInd + toInsert, spNew[toInsert])
                patternOffset = int(offsetList[index + spInd]) + len(" ".join(sentencePart[:spInd]))
                offsetList.insert(index + spInd + toInsert, str(patternOffset))
          # replace with <filler> tag
          for sIndex in range(0, len(sentenceList) - len(fl.split()) + 1):
            sentencePart = sentenceList[sIndex : sIndex + len(fl.split())]
            if " ".join(sentencePart) == fl:
              sentenceList[sIndex] = "<filler>"
              for toPopIndex in range(sIndex + 1, sIndex + len(fl.split())):
                sentenceList.pop(sIndex + 1)
                offsetList.pop(sIndex + 1)
          # update strings as well
          sentence = " ".join(sentenceList)
          offsets = " ".join(offsetList)
          break
        
  if debug == 1 and not "<filler>" in sentence:
    print "ERROR: could not find filler: " + str(item)
    continue

  sentence = re.sub(r'( <filler>)+', ' <filler>', ' ' + sentence) # replace multiple occurences (can happen with normalized dates!)
  sentence = sentence.strip()

  if slot in ["per:member_of", "per:employee_of"]:
    slot = "per:employee_or_member_of" # unify the slot names

  print docid + " :: " + posNeg + " :: " + slot + " :: " + curName + " :: " + filler + " :: " + sentence
