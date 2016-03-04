# Coreference Resolution

Usage: python Coreference_Resolution.py <indir>

Coreference_Resolution.py uses objects from CoreferenceResolutionObjects.py
The input directory should have .gold_conll files to be used for coreference resolution. The program will create gold_conll.response files for each gold_conll file and will also concatenate all gold_conll and gold_conll.response files into two master files called all_gold and all_response. The scorer can then be run on those two files. 

