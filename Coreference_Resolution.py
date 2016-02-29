import os
import sys
from CoreferenceResolutionObjects import Word, Sentence, Document
from nltk.corpus import stopwords
from collections import defaultdict

class CoreferenceResolution(object):
	def __init__(self):
		self.documents = list()
		self.stopwords = set(stopwords.words('english'))

	def add_doc(self, f, basename):
		self.documents.append(Document(f, basename))

	def write_output(self, outdir):
		for i, doc in enumerate(self.documents):
			with open(os.path.join(outdir, doc.basename)) as outfile:
				##begin document (bc/cctv/00/cctv_0000); part 000
				outfile.write("begin document (%s); part 000" % doc.basename)
				for sent in doc.sentences:
					for i, word in enumerate(sent):
						chain = '-'
						if word.chain and i > 0 and not sent[i-1].chain:
							chain = '(' + word.chain
						elif word.chain and i < len(sent) and not sent[i+1].chain:
							chain = word.chain + ')'
						elif (word.chain and i > 0 
										 and i < len(sent) 
										 and not sent[i-1].chain 
										 and not sent[i+1].chain):
							chain = '(' + word.chain + ')'

						outfile.write('\t').join([doc.basename, chain])
				outfile.write('#end document')



	def chain(self, doc, e1, e2, chain=None):
		"""make sure e1 and e2 are in the same chain in the document"""
		if e1.chain and e2.chain:
			e1_chain = e1[0].chain
			for entity in doc.chains[e2[0].chain]:
				doc.chains[e1_chain].append(entity)

		else:
			if doc.chains[chain]:
				for e in [e1, e2]:
					if e not in doc.chains[chain]:
						doc.chains[chain].append(e)
						for word in e: 
							word.chain = chain


	def string_match(self, doc, partial=False):
		matches = defaultdict(list)
		"""
		compare every entity to every other entity store matches as mapping 
		of their map number to a list each list index is the string and a 
		tuple pointing to the location of the string in the document
		{0 : ['string', (sent_num, [entity start index, end index])]}
		"""
		print doc.entities
		for i, e1 in enumerate(doc.entities):
			chained = False
			e1_words = self.resolve_entity(e1)
			for j, e2 in enumerate(doc.entities):
				#make sure we don't compare more than we have to
				#and we don't compare words already in a chain
				if j > i and e1.chain is None and e2.chain is None: 
						if e1_words == self.resolve_entity(e2):
							self.chain(doc, e1, e2, chain=i)
							chained = True
			if not chained:
				#initializie the rest of the clusters
				self.chain(doc, e1, None, i)

	def precise_constructs(self, doc, constructs=[',','is','was']):
		for i, e1 in enumerate(doc.entities):
			e1_acronym = [word.word[0] for word in e1]
			for j, e2 in enumerate(doc.entities):
				if j > i and e1[0].chain is not e2[0].chain:
					# Check appositives and and Predicate Nominatives
					if e1[0].sent_num == e2[0].sent_num:
						if (e1[-1].index + 2 == e2[0].sent_num 
						#the word between the two entities
							and doc.sentences[e1[0].sent_num][e1[-1].index + 1] in constructs):
							#combine the chains that the two entities are in
							self.chain(doc, e1, e2)
					# Check acronyms
					if e1_acronym == [word.word[0] for word in e2]:
						self.chain(doc, e1, e2)
	"""
	def partial_string_match(self, doc):
		for i, e1 in enumerate(doc.entities):
			e1_words = set([word.word for word in e1 if word not in self.stopwords])
			for j, e2 in enumerate(doc.entities):
				if j > i and e1[0].chain is not e2[0].chain: 
					# Check word inclusion
					if len(e1) > len(e2):
						if e1_words.issuperset(set(word.word for word in e2 if word not in self.stopwords))
	"""






	def resolve_entity(self, e):
		print e
		return [word.word for word in e]

	def resolve(self):
		phases = [self.string_match, #must be run first
				  self.precise_constructs
				  #self.partial_string_match()
				  ]

		for phase in phases:
			for document in self.documents:
				phase(document)

#TODO: write each phase in for seive method
# TODO: reduce redundancy resolve phases. Maybe do both enumeration for loops
# in resolve() and do the j > i and same chain check, then pass to the phase methods

if __name__ == '__main__':
	rootdir = sys.argv[1]
	search_term = 'gold_conll'

	cr = CoreferenceResolution()

	for directory, subdir, files in os.walk(rootdir):
		for fi in files:
			if fi.endswith(search_term):
				f = open(os.path.join(directory, fi))
				cr.add_doc(f, os.path.basename(fi))
	"""
	for doc in cr.documents:
		for sentence in doc.sentences:
			print [word.word for word in sentence]
	"""

	cr.resolve()
	#cr.write_output(sys.argv[2])


















