import os
import sys
from CoreferenceResolutionObjects import Word, Sentence, Document, Node, SyntaxTree

class CoreferenceResolution(object):
	def __init__(self):
		self.documents = list()

	def add_doc(self, f):
		document = []
		sentence = []
		for i, line in enumerate(f):
			if i > 0:
				if line.split():
					sentence.append(line)
				else:
					document.append(Sentence(sentence))
					sentence = []

#TODO: test sentence class

#TODO: write each phase in for seive method

if __name__ == '__main__':
	rootdir = sys.argv[1]
	search_term = sys.argv[2]

	cr = CoreferenceResolution()

	for directory, subdir, files in os.walk(rootdir):
		for fi in files:
			if fi.endswith(search_term):
				f = open(os.path.join(directory, fi))
				cr.add_doc(f)
