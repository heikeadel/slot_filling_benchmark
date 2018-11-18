#!/usr/bin/python

# File name: utilities.py
# Author: Heike Adel
# Date: January 2016

import sys
import string
import re
import os


string2number = {'one' : '1', 'two' : '2', 'three' : '3', 'four' : '4', 'five' : '5', 'six' : '6',
                 'seven' : '7', 'eight' : '8', 'nine' : '9', 'ten' : '10', 'eleven' : '11', 'twelve' : '12'}

def cleanSentence(sentence):
  # clean sentences from HTML tags
  toClean = []
  sentenceList = sentence.split()
  inHtmlTag = 0
  for indWord, curWord in enumerate(sentenceList):
    if inHtmlTag == 1:
      toClean.append(indWord)
      if re.search(r'\>$', curWord):
        inHtmlTag = 0
      continue
    if curWord[0] == '<' and curWord[-1] == '>' and curWord != "<filler>" and curWord != "<name>":
      toClean.append(indWord)
      continue
    if inHtmlTag == 0 and re.search(r'^\<DOC', curWord):
      toClean.append(indWord)
      inHtmlTag = 1
      continue
  toCleanSorted = sorted(toClean, reverse = True)
  for curKey in toCleanSorted:
    sentenceList.pop(curKey)
  sentenceCleaned = " ".join(sentenceList)
  return sentenceCleaned

def month2year(month):
  result = ""
  if month in string2number:
    month = string2number[month]
  if month.isdigit():
    result = str(int(month) / 12)
  return result

def tokenizeNames(nameListOrig, coreNLPpath):
  # tokenize names to the same format as the texts will be tokenized
  curPwd = os.getcwd()
  nameList = []
  os.chdir(coreNLPpath)
  for n in nameListOrig:
    if re.search(r'[^a-zA-Z ]', n):
      nameOut = open(curPwd + '/name.forTok', 'w')
      nameOut.write(n + "\n")
      nameOut.close()
      os.system("java -cp stanford-corenlp-3.3.1.jar:stanford-corenlp-3.3.1-models.jar:xom.jar:joda-time.jar:jollyday.jar:ejml-0.23.jar -Xmx3g edu.stanford.nlp.process.PTBTokenizer " + curPwd + "/name.forTok > " + curPwd + "/name.afterTok")
      nameIn = open(curPwd + '/name.afterTok', 'r')
      nameTok = ""
      for line in nameIn:
        line = line.strip()
        nameTok += line + " "
      nameTok = nameTok.strip()
      nameTok = re.sub(r'( \.$)+', '', nameTok)
      nameList.append(nameTok)
      nameIn.close()
    else:
      nameList.append(n)
  os.chdir(curPwd)

  sys.stderr.write("tokenized " + str(nameListOrig) + " to " + str(nameList) + "\n")
  return nameList

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n

    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)

    return current[n]

def getCapitalizationList(text):
  result = []
  for word in text.split():
    if word[0].isupper():
      result.append(1)
    else:
      result.append(0)
  return result

def compareNames(name, myText):
  myTextOrig = myText
  nameOrig = name
  nameIsAcronym = 0
  myTextOrigList = myText.split()
  capitalizationName = getCapitalizationList(name)
  capitalizationMyText = getCapitalizationList(myText)
  if name.isupper():
    nameIsAcronym = 1
  else:
    myText = string.lower(myText).strip()
    name = string.lower(name).strip()
  nameList = name.split()
  lengthName = len(nameList)
  myTextList = myText.split()
  lengthText = len(myTextList)
  resultHits = []
  for t in range(0, lengthText - lengthName + 1):
    testName = " ".join(myTextList[t:t+lengthName])
    if testName == name:
      # exact match
      if nameIsAcronym:
        testNameOrig = " ".join(myTextOrigList[t:t+lengthName])
        if testNameOrig.isupper(): # match only with acronyms!
          resultHits.append([t, t+lengthName])
      else:
        # compare uppercase letters only with upper case letters!
        noMatch = 0
        for ind, cn in enumerate(capitalizationName):
          if cn != capitalizationMyText[t + ind]:
            noMatch = 1
            break
        if noMatch == 1:
          sys.stderr.write("INFO: no match: " + nameOrig + " <=> " + myTextOrig + "\n")
          continue
        resultHits.append([t, t+lengthName])
    else:
      # fuzzy match
      charactersName = list(name)
      charactersMyText = list(testName)
      maxDistance = max(1, len(charactersName) / 7) # just some heuristic
      if len(charactersName) < 2 or len(charactersMyText) < 2 or abs(len(charactersName) - len(charactersMyText)) > maxDistance:
        continue
      distanceNames = levenshtein(name, testName)
      if distanceNames > maxDistance:
        continue
      else:
        if nameIsAcronym:
          testNameOrig = " ".join(myTextOrigList[t:t+lengthName])
          if testNameOrig.isupper(): # match only with acronyms!
            sys.stderr.write("INFO: found similar but not equal names: " + name + " - " + testNameOrig + "\n")
            resultHits.append([t, t+lengthName])
        else:
          if capitalizationName.count(1) == capitalizationMyText[t:t+lengthName].count(1):  
            # heuristic: in matched text must be the same number of uppercase letters as in name!
            sys.stderr.write("INFO: found similar but not equal names: " + name + " - " + testName + "\n")
            resultHits.append([t, t+lengthName])
          else:
            sys.stderr.write("INFO: no match: " + nameOrig + " <=> " + myTextOrig + "\n")
            continue
  return resultHits

def getIndexOfName(sentence, alias, sign):
  aliasLength = len(alias.split())
  sentenceList = sentence.split()
  for i in range(0, len(sentenceList) - aliasLength + 1):
    sentencePart = " ".join(sentenceList[i : i + aliasLength])
    sentencePart = re.sub(r'' + sign, ' ', sentencePart)
    if ' ' + alias + ' ' in ' ' + sentencePart + ' ':
      return i
  return -1

def getFillerList(filler, synonyms):
  fillerList = [filler]
  if re.search(r'[a-zA-Z0-9]', filler): # only append filler with alphanumeric characters
    if filler in synonyms:
      fillerSynonyms = synonyms[filler]
      fillerList.extend(fillerSynonyms)
    if filler.isupper():
      fillerTitle = filler.title()
      fillerList.append(fillerTitle)
    if "_" in filler: # and not " " in filler:
      # replace "_" with spaces
      filler2 = re.sub(r'\_', ' ', filler)
      fillerList.append(filler2)
    if not " " in filler:
      # replace camel case fillers with fillers with spaces
      filler2 = re.sub(r'([A-Z])', ' \\1', filler)
      filler2 = filler2.strip()
      fillerList.append(filler2)
  fillerList = list(set(fillerList))
  return fillerList

def updateBestIndices(bestIndices, hits):
  for hit in hits:
    start = hit[0]
    end = hit[1]
    foundRange = 0
    for hitInd, h in enumerate(bestIndices):
      # test whether there is an overlap at all
      if (start <= h[0] and end >= h[0]) or (start <= h[1] and end >= h[1]) or (start <= h[0] and end >= h[1]) or (start >= h[0] and end <= h[1]):
        foundRange = 1
        # test whether the current indices are better than the old ones
        if start <= h[0] and end >= h[1]:
          bestIndices[hitInd] = [start, end]
        elif start > h[0] and start < h[1] and end >= h[1]: # extend to the right
          bestIndices[hitInd] = [h[0], end]
        elif start <= h[0] and end < h[1] and end >= h[0]: # extend to the left
          bestIndices[hitInd] = [start, h[1]]

    if foundRange == 0:
      bestIndices.append([start, end]) # found additional occurrence of name

def nerTest(bestStart, bestEnd, nerList, sentenceList, slot):
  bestEndNerTest = bestEnd
  if "org:" in slot and bestEnd < len(sentenceList) - 1 and sentenceList[bestEnd] in ['Corp', 'Corp.', 'Inc', 'Inc.', 'Corporation', 'Corps', 'Co']:
    bestEndNerTest = bestEnd + 1
  if "MISC" in nerList[bestStart : bestEndNerTest] or "SET" in nerList[bestStart : bestEndNerTest] or nerList[bestStart] != nerList[bestEndNerTest - 1]:
    return 1 # no statement possible
  if nerList[bestStart] == 'O' or ((bestStart == 0 or nerList[bestStart] != nerList[bestStart - 1] or sentenceList[bestStart - 1] in ["Dear", "Sheik", "Sheikh", "Prof", "Prof.", "Imam", "Dr", "Dr."]) and (bestEndNerTest - 1 >= len(sentenceList) - 1 or nerList[bestEndNerTest - 1] != nerList[bestEndNerTest])):
    return 1
  else:
    if (bestStart == 0 or nerList[bestStart] != nerList[bestStart - 1] or sentenceList[bestStart - 1] in ["and", "of", "'s"]) and (bestEndNerTest - 1 >= len(sentenceList) - 1 or nerList[bestEndNerTest - 1] != nerList[bestEndNerTest] or sentenceList[bestEndNerTest] in ["and", "'s", "of"]):
      return 1 # two successive organizations are often tagged as being one organization
    else:
      return 0

def cleanWord(word):
  word = re.sub(r'\`\`', '"', word)
  word = re.sub(r'\`', "'", word)
  word = re.sub(r'\xc2\x92\xc2\x94', "'''", word)
  word = re.sub(r"\'\'", '"', word)
  word = re.sub(r'\xe2\x80\x9c', '"', word)
  word = re.sub(r'\xe2\x80\x9d', '"', word)
  word = re.sub(r'\xe2\x80\x99', "'", word)
  word = re.sub(r'\xc2\x93', '"', word)
  word = re.sub(r'\xc2\x94', '"', word)
  word = re.sub(r'\xc2\x91', "'", word)
  word = re.sub(r'\xc2\xbb', '"', word)
  word = re.sub(r'&quot;', '"', word)
  word = re.sub(r'\&gt\;', '>', word)
  word = re.sub(r'\&lt\;', '<', word)
  word = re.sub(r'&amp;', '&', word)
  word = re.sub(r'\xc2\xa4', '$', word)
  word = re.sub(r'\xe2\x80\x94', '--', word)
  word = re.sub(r'\xc2\x97', "--", word)
  word = re.sub(r'\xc2\x96', "--", word)
  word = re.sub(r'\xe2\x80\x93', '--', word)
  word = re.sub(r'\xe2\x80\x95', '--', word)
  word = re.sub(r'\xc2\x92', "'", word)
  word = re.sub(r'\xc2\x85', '..', word)
  word = re.sub(r'\xe2\x80\x98', "'", word)
  word = re.sub(r'\-LRB\-', '(', word)
  word = re.sub(r'\-RRB\-', ')', word)
  word = re.sub(r'\-LCB\-', '{', word)
  word = re.sub(r'\-RCB\-', '}', word)
  word = re.sub(r'\-LSB\-', '[', word)
  word = re.sub(r'\-RSB\-', ']', word)
  word = re.sub(r'\xc2\x80', '$', word)
  word = re.sub(r'\xe2\x82\xac', '$', word)
  word = re.sub(r'\xe2\x80\xa6', '...', word)
  word = re.sub(r'\xc2\xa2', 'cents', word)
  word = re.sub(r'\xc2\xa3', '#', word) # CoreNLP does the same internally
  word = re.sub(r'\xc2\xbd', '1/2', word)
  word = re.sub(r'\xc2\xbe', '3/4', word)
  word = re.sub(r'\xc2\xbc', '1/4', word)
  word = re.sub(r'\xe2\x80\xba', "'", word)
  word = re.sub(r'\xe2\x80\xb9', "'", word)
  word = re.sub(r'\xc2\xab', '"', word)
  word = re.sub(r'\xe3\x80\x80', '', word)
  word = re.sub(r'\xe3\x80\x8c', '', word)
  word = re.sub(r'\xe3\x80\x8d', '', word)
  return word

