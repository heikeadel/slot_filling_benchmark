#!/usr/bin/python

# File name: splitYearwise.py
# Author: Heike Adel
# Date: January 2016

import re
import sys
from configClass import Config

if len(sys.argv) != 2:
  print "please pass the file with the extracted assessment data as argument"
  exit()

inputfile = sys.argv[1]

# get information which name was part of the evaluation of which year
config = Config()
name2year = {}
for year in config.queryFiles:
  queryfile = config.queryFiles[year]
  f = open(queryfile, 'r')
  for line in f:
    line = line.strip()
    if "<name>" in line:
      name = re.sub(r'^\s*\<name\>(.*?)\<\/name\>\s*$', '\\1', line)
      name2year[name] = year
  f.close()

f = open(inputfile, 'r')
year2data = {}
for line in f:
  line = line.strip()
  name = line.split(' :: ')[3]
  if not name in name2year:
    print "ERROR: unknown name: " + name
    continue
  year = name2year[name]
  if not year in year2data:
    year2data[year] = []
  year2data[year].append(line)
f.close()

for year in year2data:
  out = open(inputfile + "." + year, 'w')
  for item in year2data[year]:
    out.write(item + "\n")
  out.close()
