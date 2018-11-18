#!/usr/bin/python

# File name: cleanData.py
# Author: Heike Adel
# Date: January 2016

from utilities import cleanSentence
import sys

if len(sys.argv) != 2:
  print "please pass the file to be cleaned as parameter"
  exit()

f = open(sys.argv[1], 'r')
for line in f:
  line = line.strip()
  line2 = cleanSentence(line)
  print line2
f.close()
