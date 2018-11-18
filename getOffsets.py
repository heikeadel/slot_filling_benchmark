#!/usr/bin/python

# File name: getOffsets.py
# Author: Heike Adel
# Date: January 2016

import gzip
import re
from utilities import cleanWord

def using_split(line):
    words = line.split()
    offsets = []
    running_offset = 0
    for word in words:
        word_offset = line.index(word, running_offset)
        word_len = len(word)
        running_offset = word_offset + word_len
        offsets.append([word, word_offset, running_offset])
    return offsets


def getOffsets(docId, docPath):
  if ".gz" in docPath:
    f = gzip.open(docPath)
  else:
    f = open(docPath)
  lastOffset = 0
  readDoc = 0
  results = []
  startOfDocument = ""
  for line in f:
    if ("<doc" in line or "<DOC" in line) and not "id" in line and not "ID" in line:
      startOfDocument += line
    if 'id="' + docId + '"' in line or 'DOCID> ' + docId in line:
      readDoc = 1
      # get offsets for start of document:
      result = using_split(startOfDocument)
      for r in range(len(result)):
        result[r][1] += lastOffset
        result[r][2] += lastOffset
      if len(result) > 0:
        lastOffset = result[-1][2] + 1
        results.extend(result)
    if readDoc == 1:
      line = re.sub(r'\xc2\xa0', ' ', line)
      line = re.sub(r'\xe2\x80\x82', ' ', line)
      line = re.sub(r'\xe2\x80\x85', ' ', line)
      line = re.sub(r'\xe2\x80\x89', ' ', line)
      # the following characters are untokenizable by CoreNLP and are skipped in counting offsets
      line = re.sub(r'\xc2\x95', '', line)
      line = re.sub(r'\xe2\x80\x83', '', line)
      line = re.sub(r'\xc2\x99', '', line)
      line = re.sub(r'\xc2\x9e', '', line)
      line = re.sub(r'\xc2\x9c', '', line)
      line = re.sub(r'\xc2\x82', '', line)
      line = re.sub(r'\xc2\x98', '', line)
      line = re.sub(r'\xc2\xad', '', line)
      line = re.sub(r'\xef\x81\x82', '', line)
      line = re.sub(r'\xef\xbf\xbd', '', line)
      line = re.sub(r'\xe2\x80\xa8', '', line)
      result = using_split(line)
      for r in range(len(result)):
        result[r][1] += lastOffset
        result[r][2] += lastOffset
      if len(result) > 0:
        lastOffset = result[-1][2] + 1
        results.extend(result)
      else:
        lastOffset += 1
    if "</DOC>" in line or "</doc>" in line:
      if readDoc == 1:
        break
      else:
        startOfDocument = ""
  f.close()
  return results

def correctOffsets(docid, docpath, textPerLine, offsetsPerLine, offset2NormNer):
  pythonOffsetResults = getOffsets(docid, docpath)
  indOuterList = 0
  indCoreNLP = 0
  indPython = 0
  curOffsetList = offsetsPerLine[indOuterList].split()
  adjustTerm = 0
  newOffsetsPerLine = []
  newOffset2NormNer = {}
  curLineOffsets = ""
  prevPythonWord = ""
  prevPythonWordCleaned = ""
  while indPython < len(pythonOffsetResults):
    if indCoreNLP >= len(curOffsetList):
      # store updated offsets and get list from next line
      newOffsetsPerLine.append(curLineOffsets.strip())
      indOuterList += 1
      if indOuterList >= len(offsetsPerLine):
        curLineOffsets = ""
        break # everything should have been appended already
      curOffsetList = offsetsPerLine[indOuterList].split()
      indCoreNLP = 0
      curLineOffsets = ""
    pythonStartOffset = pythonOffsetResults[indPython][1]
    pythonWord = pythonOffsetResults[indPython][0]
    coreNLPStartOffset = int(curOffsetList[indCoreNLP]) + adjustTerm
    curWord = textPerLine[indOuterList].split()[indCoreNLP]
    if pythonStartOffset < coreNLPStartOffset:
      prevWord = ""
      if indCoreNLP > 0:
        prevWord = textPerLine[indOuterList].split()[indCoreNLP-1]
      prevWord = cleanWord(prevWord)
      curWord = cleanWord(curWord)
      if prevWord + curWord in prevPythonWordCleaned:
        # adjust coreNLP offset backwards (decoding issue?)
        adjustTerm += pythonStartOffset - coreNLPStartOffset
        coreNLPStartOffset += pythonStartOffset - coreNLPStartOffset
        coreNLPStartOffset -= len(curWord)
        curLineOffsets += str(coreNLPStartOffset) + " "
        if curOffsetList[indCoreNLP] in offset2NormNer:
          newOffset2NormNer[str(coreNLPStartOffset)] = str(offset2NormNer[curOffsetList[indCoreNLP]])
        indCoreNLP += 1
        continue
      if curWord in cleanWord(pythonWord) or cleanWord(curWord) in cleanWord(pythonWord):
        # adjust coreNLP offset backwards (decoding issue?)
        adjustTerm += pythonStartOffset - coreNLPStartOffset
        coreNLPStartOffset += pythonStartOffset - coreNLPStartOffset
        curLineOffsets += str(coreNLPStartOffset) + " "
        if curOffsetList[indCoreNLP] in offset2NormNer:
          newOffset2NormNer[str(coreNLPStartOffset)] = str(offset2NormNer[curOffsetList[indCoreNLP]])
        indCoreNLP += 1
      indPython += 1
      prevPythonWord = pythonWord
      prevPythonWordCleaned = cleanWord(pythonWord)
      continue
    if pythonStartOffset == coreNLPStartOffset and (pythonWord[0] == curWord[0] or cleanWord(pythonWord)[0] == cleanWord(curWord)[0]):
      curLineOffsets += str(coreNLPStartOffset) + " "
      if curOffsetList[indCoreNLP] in offset2NormNer:
        newOffset2NormNer[str(coreNLPStartOffset)] = str(offset2NormNer[curOffsetList[indCoreNLP]])
      indCoreNLP += 1
      indPython += 1
      prevPythonWord = pythonWord
      prevPythonWordCleaned = cleanWord(pythonWord)
      continue
    if pythonStartOffset >= coreNLPStartOffset:
      prevWord = ""
      if indCoreNLP > 0:
        prevWord = textPerLine[indOuterList].split()[indCoreNLP-1]
      prevWord = cleanWord(prevWord)
      curWord = cleanWord(curWord)
      if indCoreNLP + 1 < len(textPerLine[indOuterList].split()):
        nextWord = textPerLine[indOuterList].split()[indCoreNLP+1]
        if curWord == '-' and ((prevWord == 'etc.' and nextWord == '(') or (prevWord == '=' and nextWord == '=' and not '-' in prevPythonWord) or (prevWord == 'Fe' and nextWord == 'ith') or (prevWord == '2008' and nextWord == 'ViewFinders') or (prevWord == '22' and nextWord == '26') or (prevWord == '10' and nextWord == '14') or (prevWord == '1pm' and nextWord == '4pm') or (re.search(r'\xc2\xa1', prevWord) and nextWord == '.') or (prevWord == '6:00' and nextWord == '8:00') or (prevWord == 'novice' and nextWord == 'or') or (prevWord == 'noon' and nextWord == '7:00')):
          # the word - has been inserted by CoreNLP -> delete it!
          curWord = nextWord
          indCoreNLP += 1
          coreNLPStartOffset = int(curOffsetList[indCoreNLP]) + adjustTerm
      if (prevWord + curWord in prevPythonWord or
         prevWord + curWord in prevPythonWordCleaned or
         cleanWord(prevWord + curWord) in prevPythonWordCleaned or
         cleanWord(prevWord + curWord) in cleanWord(prevPythonWordCleaned) or
         re.sub(r'\.\.', '.', prevWord + curWord) in prevPythonWord or
         re.sub(r'\.\.', '.', prevWord + curWord) in prevPythonWordCleaned or
         re.sub(r'\.\.\.', '.', prevWord + curWord) in prevPythonWord or
         re.sub(r'\.\.\.', '.', prevWord + curWord) in prevPythonWordCleaned or
         re.sub(r'\"', "''", prevWord + curWord) in re.sub(r'\"', "''", prevPythonWordCleaned) or
         ((prevWord + curWord)[-1] == prevPythonWordCleaned[-1])):
        pass
      else:
        adjustTerm += pythonStartOffset - coreNLPStartOffset
        # adjust coreNLPOffsets
        coreNLPStartOffset += pythonStartOffset - coreNLPStartOffset
        indPython += 1
        prevPythonWord = pythonWord
        prevPythonWordCleaned = cleanWord(pythonWord)
      # store new offset for coreNLP
      curLineOffsets += str(coreNLPStartOffset) + " "
      if curOffsetList[indCoreNLP] in offset2NormNer:
        newOffset2NormNer[str(coreNLPStartOffset)] = str(offset2NormNer[curOffsetList[indCoreNLP]])
      indCoreNLP += 1
      continue
  if curLineOffsets != "":
    newOffsetsPerLine.append(curLineOffsets.strip()) # append everything which has not been appended so far
  if len(offsetsPerLine) != len(newOffsetsPerLine):
    newOffsetsPerLine = []
  return [newOffsetsPerLine, newOffset2NormNer]
