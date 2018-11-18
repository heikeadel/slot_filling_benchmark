# Overview

Program for extracting SF benchmark data,

written by Heike Adel, CIS, LMU Munich

version 1.0, 2016

# Description

In the following, the different components of the program are described:

DO.getAssessmentData:
The program can be easily executed by just running the DO.getAssessmentData script.

configClass.py:
BEFORE running the program, please set the paths in the configClass file according to your system environment.
Preliminaries:
- In order to run the program, the Stanford CoreNLP toolkit [1] is needed.
  It can be downloaded at http://nlp.stanford.edu/software/corenlp.shtml

entitiesManager.py:
The class Entities provides every information needed about the entities in the SF query files, e.g. their aliases and gender.

getData.py:
This script provides the main function of the program and is directly called by the DO.getAssessmentData file.

getOffsets.py:
In these functions, the offsets obtained by the Stanford CoreNLP toolkit are adapted according to their proper values (including every whitespace, etc.)

openAndTokenizeDoc.py:
This script calls the Stanford CoreNLP toolkit in order to get the following information for the given document:
- offsets
- tokenized text
- named entity information
- normalized dates

resourceManager.py:
The class Resources provides every information from additional resources, e.g. the doc2pathfile, synonyms for fillers, etc.

utilities.py:
This script collects basic utilities functions used at various steps during the program, e.g. tokenization of names, fuzzy name match, data cleaning, etc.

### Additional scripts for splitting the data into dev and eval sets
splitGenreIntoDevAndEval.py:
This script splits the extracted data into genre wise dev and eval sets

splitYearwise.py:
This script splits the extracted data into years; then the 2012+2013 data can be selected as dev and 2014 as eval data

### Encoding
Please note that the provided scripts do not use utf-8 encoding by default.
This is because a utf-8 version of the program was not able to extract as many examples as this version (the number of extractions was 5292 (16%) less).

# References
[1] Stanford CoreNLP toolkit:
Manning, Christopher D., Surdeanu, Mihai, Bauer, John, Finkel, Jenny, Bethard, Steven J., and McClosky, David: The Stanford CoreNLP Natural Language Processing Toolkit. In ACL: System Demonstrations, pp. 55-60, 2014.

# Contact
If you have questions, please contact heike.adel@ims.uni-stuttgart.de

# Citation
Citing this program:
If you use this program, please cite the following paper:

```
@inproceedings{adelSF2016,
  title={Comparing Convolutional Neural Networks to Traditional Models for Slot Filling},
  author={Heike Adel and Benjamin Roth and Hinrich Sch\"{u}tze},
  year={2016},
  booktitle={{NAACL} {HLT} 2016, The 2016 Conference of the North American Chapter
               of the Association for Computational Linguistics: Human Language Technologies,
               San Diego, California, USA, June 12 - June 17, 2016}
}
```
