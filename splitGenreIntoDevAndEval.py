#!/usr/bin/python

# File name: splitGenreIntoDevAndEval.py
# Author: Heike Adel
# Date: January 2016

import sys

if len(sys.argv) != 3:
  print "please pass the file with extracted data and the output directory as input parameter"
  exit()
inputfile = sys.argv[1]
outputdir = sys.argv[2]

newsDevFile = "indices_newsDev"
newsEvalFile = "indices_newsEval"
webDevFile = "indices_webDev"
webEvalFile = "indices_webEval"

newsDev = []
newsEval = []
webDev = []
webEval = []

# read information about how to split
f = open(newsDevFile, 'r')
for line in f:
  line = line.strip()
  parts = line.split(' :: ')
  newsDev.append(parts)
f.close()
f = open(newsEvalFile, 'r')
for line in f:
  line = line.strip()
  parts = line.split(' :: ')
  newsEval.append(parts)
f.close()
f = open(webDevFile, 'r')
for line in f:
  line = line.strip()
  parts = line.split(' :: ')
  webDev.append(parts)
f.close()
f = open(webEvalFile, 'r')
for line in f:
  line = line.strip()
  parts = line.split(' :: ')
  webEval.append(parts)
f.close()

# prepare output files
outNewsDev = open(outputdir + '/news.dev', 'w')
outNewsEval = open(outputdir + '/news.eval', 'w')
outWebDev = open(outputdir + '/web.dev', 'w')
outWebEval = open(outputdir + '/web.eval', 'w')

# split extracted data
f = open(inputfile, 'r')
for line in f:
  line = line.strip()
  parts = line.split(' :: ')
  relevantParts = parts[0:5] + parts[5].split()[0:2] + parts[5].split()[-2:]
  if relevantParts in newsDev:
    outNewsDev.write(line + "\n")
  elif relevantParts in newsEval:
    outNewsEval.write(line + "\n")
  elif relevantParts in webDev:
    outWebDev.write(line + "\n")
  elif relevantParts in webEval:
    outWebEval.write(line + "\n")
  else:
    if not "bolt-" in parts[0]:
      print line
f.close()

outNewsDev.close()
outNewsEval.close()
outWebDev.close()
outWebEval.close()
