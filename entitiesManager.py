#!/usr/bin/python

# File name: entitiesManager.py
# Author: Heike Adel
# Date: January 2016

import re
import copy
import string
from utilities import tokenizeNames
from configClass import Config

# this class manages the whole set of entities

class Entities:

  ########### methods ###############################

  def readGender2Name(self):
    name2gender = {}
    f = open(self.genderFile, 'r')
    for line in f:
      line = line.strip()
      parts = line.split()
      name = parts[0]
      gender = parts[1]
      name2gender[name] = gender
    f.close()
    return name2gender

  def getGenderForEntity(self, name):
    return self.name2gender[name]

  def completeListOfAlias(self, curName, slot):
    listOfAliasTmp = []
    if "org:" in slot:
      if "Organization" in curName:
        alias = re.sub(r'Organization', 'Corporation', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Organization', 'Corp', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Organization', 'Corps', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Organization', 'Co', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Organization', '', curName)
        alias = alias.strip()
        listOfAliasTmp.append(alias)
      elif "Corporation" in curName:
        alias = re.sub(r'Corporation', 'Corps', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corporation', 'Corp', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corporation', 'Co', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corporation', 'Organization', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corporation', '', curName)
        alias = alias.strip()
        listOfAliasTmp.append(alias)
      elif " Corps" in curName:
        alias = re.sub(r'Corps', 'Corporation', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corps', 'Corp', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corps', 'Co', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corps', 'Organization', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corps', '', curName)
        alias = alias.strip()
        listOfAliasTmp.append(alias)
      elif " Corp" in curName:
        alias = re.sub(r'Corp', 'Corporation', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corp', 'Corps', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corp', 'Co', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corp', 'Organization', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Corp', '', curName)
        alias = alias.strip()
        listOfAliasTmp.append(alias)
    else:
      # add name without middle names:
      nameParts = curName.split()
      alias = ""
      if len(nameParts) > 2:
        alias = nameParts[0] + " " + nameParts[-1]
      listOfAliasTmp.append(alias)
      # add name without middle initial:
      alias = ""
      for np in nameParts:
        if len(np) == 2 and "." in np:
          continue
        elif len(np) > 1:
          alias += np + " "
      alias = alias.strip()
      listOfAliasTmp.append(alias)
      # add name splitted at hyphen
      if "-" in curName:
        alias = re.sub(r'\s*\-\s*', ' ', curName)
        listOfAliasTmp.append(alias)
      if " Jr." in curName:
        alias = re.sub(r'Jr\.', 'Junior', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Jr\.', 'Jr', curName)
        listOfAliasTmp.append(alias)
      elif " Jr" in curName:
        alias = re.sub(r'Jr', 'Junior', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Jr', 'Jr.', curName)
        listOfAliasTmp.append(alias)
      elif " Junior" in curName:
        alias = re.sub(r'Junior', 'Jr.', curName)
        listOfAliasTmp.append(alias)
        alias = re.sub(r'Junior', 'Jr', curName)
        listOfAliasTmp.append(alias)
    return listOfAliasTmp

  def getName2Alias(self, data):

    noAcronyms = [] # list of abbreviations which are also states or countries - should not be used as acronym for a company
    f = open(self.config.noAcronymFile, 'r')
    for line in f:
      line = line.strip()
      noAcronyms.append(line)
    f.close()

    name2alias = {}
    for item in data:
      slot = item[1]
      curName = item[2]
      if curName in name2alias:
        continue
      listOfAlias = self.getAlias(curName)
      while curName in listOfAlias:
        listOfAlias.remove(curName)
      listOfAlias.insert(0, curName)
      if "org:" in slot:
        # search for name also without Organization/Corp extension
        curNameWithoutDots = re.sub(r'\.', '', curName)
        curNameWithoutDots = " " + curNameWithoutDots + " "
        newAlias = ""
        if " Organization " in curNameWithoutDots:
          newAlias = re.sub(r' Organization', '', curNameWithoutDots)
        elif " Corps " in curNameWithoutDots:
          newAlias = re.sub(r' Corps', '', curNameWithoutDots)
        elif " Co " in curNameWithoutDots:
          newAlias = re.sub(r' Co', '', curNameWithoutDots)
        elif " Corporation " in curNameWithoutDots:
          newAlias = re.sub(r' Corporation', '', curNameWithoutDots)
        elif " Corp " in curNameWithoutDots:
          newAlias = re.sub(r' Corp', '', curNameWithoutDots)
        elif "Inc." in curNameWithoutDots:
          newAlias = re.sub(r' Inc\.', '', curNameWithoutDots)
        elif " Inc" in curNameWithoutDots:
          newAlias = re.sub(r' Inc', '', curNameWithoutDots)
        elif " Association of " in curNameWithoutDots:
          newAlias = re.sub(r' Association of ', '', curNameWithoutDots)
        newAlias = newAlias.strip()
        if newAlias != "" and not newAlias in listOfAlias:
          listOfAlias[0] = newAlias
        # spelling variation of 'center'
        if " Center " in curNameWithoutDots:
          newAlias = re.sub(r' Center ', ' Centre ', curNameWithoutDots)
          newAlias = newAlias.strip()
          if not newAlias in listOfAlias:
            listOfAlias.append(newAlias)
        elif " Centre " in curNameWithoutDots:
          newAlias = re.sub(r' Centre ', ' Center ', curNameWithoutDots)
          newAlias = newAlias.strip()
          if not newAlias in listOfAlias:
            listOfAlias.append(newAlias)
        if " Cruise Lines " in curNameWithoutDots:
          newAlias = re.sub(r' Cruise Lines ', '', curNameWithoutDots)
          newAlias = newAlias.strip()
          if not newAlias in listOfAlias:
            listOfAlias.append(newAlias)
        # add additional alias: acronym
        acronym = ""
        for part in curName.split():
          if part[0].isupper():
            acronym += part[0]
        acronymLc = string.lower(acronym)
        if len(acronymLc.split()) > 0 and len(acronymLc.split()) < 2 and not acronymLc in noAcronyms and not acronym in listOfAlias:
          listOfAlias.append(acronym)
        # cut 'of XX' off name
        if re.search(r'^(.*?) of (.*?)$', curName):
          newAlias = re.sub(r'^(.*?) of (.*?)$', '\\1', curName)
          if not newAlias in listOfAlias:
            listOfAlias.append(newAlias)

      listOfAlias2 = []
      if listOfAlias[0] != curName:
        firstAlias = listOfAlias[0]
        listOfAlias.insert(0, curName) # if Inc/Corp etc extension has been removed: add original curName again to list of names!
        listOfAlias2.extend(self.getAlias(firstAlias)) # get alias for curName without Inc/Corp etc extension
      listOfAlias2.extend(self.completeListOfAlias(curName, slot))
      for al in listOfAlias2:
        if not al in listOfAlias:
          listOfAlias.append(al)
      if "org:" in slot:
        furtherAlias = []
        for al in listOfAlias:
          for word in al.split():
            if re.search(r'^[A-Z]+$', word): # possible abbreviation of name
              if not word in listOfAlias and not word in furtherAlias: # add as single alias
                furtherAlias.append(word)
        listOfAlias.extend(furtherAlias)

      if "per:" in slot: # also append first and last name
        curNameParts = curName.split()
        firstName = curNameParts[0]
        firstName2 = " ".join(curNameParts[:-1])
        lastName = curNameParts[-1]
        listOfAlias.append(firstName)
        listOfAlias.append(firstName2)
        listOfAlias.append(lastName)

      listOfAliasOrig = copy.deepcopy(listOfAlias)
      for la in listOfAliasOrig:
        if not re.search(r'[a-zA-Z]', la): # do not allow numbers or symbols as names
          listOfAlias.remove(la)
      listOfTokenizedAlias = tokenizeNames(listOfAlias, self.config.coreNLPpath)

      name2alias[curName] = listOfTokenizedAlias
    return name2alias

  def getAlias(self, curName):
    aliasList = []
    if curName in self.nameToBaseName:
      basename = self.nameToBaseName[curName]
      aliasList = self.baseNameToAliasList[basename]
    return aliasList



  ########## constructor ############################

  def __init__(self, assessments, baseNameToAliasList, nameToBaseName):
    self.config = Config()
    self.baseNameToAliasList = baseNameToAliasList
    self.nameToBaseName = nameToBaseName
    self.genderFile = self.config.name2genderFile
    # extract and extend aliases for the query entities
    self.name2alias = self.getName2Alias(assessments)

    # get gender information for first names
    self.name2gender = self.readGender2Name()

