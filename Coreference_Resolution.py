import os
import sys
from CoreferenceResolutionObjects import Word, Sentence, Document
from nltk.corpus import stopwords
from collections import defaultdict

class CoreferenceResolution(object):
	def __init__(self):
		self.documents = list()
		self.stopwords = set(stopwords.words('english'))
		self.pronouns = set(p.lower() for p in ['all', 'another', 'any', 'anybody', 
			'anyone', 'anything', 'both', 'each', 'either', 'everybody', 'everyone', 
			'everything', 'few', 'he', 'her', 'hers', 'herself', 'him', 'himself', 
			'his', 'I', 'it', 'its','itself', 'many', 'me', 'mine', 'more', 'most', 
			'much', 'my', 'myself', 'neither', 'no', 'one', 'nobody', 'none', 'nothing', 
			'one', 'other', 'others', 'our', 'ours', 'ourselves', 'several', 'she', 
			'some', 'somebody', 'someone','something', 'that', 'their', 'theirs', 'them', 
			'themselves', 'these','they', 'this', 'those', 'us', 'we', 'what', 'whatever', 
			'which', 'whichever','who', 'whoever', 'whom', 'whomever', 'whose', 'you', 
			'your', 'yours', 'yourself', 'yourselves'])

	def add_doc(self, f, basename):
		self.documents.append(Document(f, basename))

	def write_output(self, search_term='gold_conll', response_term='gold_conll'):
		for doc in self.documents:
			auto_path = ''.join([doc.basename.split(search_term)[0]] + [response_term])
			#print auto_path
			auto_file = open(auto_path)
			response = open(doc.basename + '.response', 'w+')
			mentions = []
			for sent in doc.sentences:
				for i, word in enumerate(sent.words):
					chain = '-'
					if word.chain:
						if i == 0 and sent.words[i+1] and not sent.words[i+1].chain:
							chain = '(' + str(word.chain) + ')'
						elif i == len(sent.words) and sent.words[i-1] and not sent.words[i-1].chain:
							chain = '(' + str(word.chain) + ')'
						elif (i > 0 and i < len(sent.words)
								   and not sent.words[i-1].chain
								   and not sent.words[i+1].chain):
							chain = '(' + str(word.chain) + ')'
						elif word.chain and i > 0 and not sent.words[i-1].chain:
							chain = '(' + str(word.chain)
						elif word.chain and i == 0:
							chain = '(' + str(word.chain)
						elif word.chain and i <= len(sent.words) and not sent.words[i+1].chain:
							chain = str(word.chain) + ')'
					mentions.append(chain)
			for line in auto_file:
				if line.startswith('#'):
					pass
				elif line.split():
					line = line.split()
					line[-1] = mentions.pop(0)
					line = '\t'.join(line)
					
				#print line
				response.write(line + "\n")


	def old_write_output(self, outdir):
		for i, doc in enumerate(self.documents):
			part = "0"
			outfile = open(''.join([doc.basename, '.response']), 'w+')
			outfile.write("#begin document (Test); %s\n" % ("00" + str(part))[-3:])
			for sent in doc.sentences:
				for i, word in enumerate(sent.words):
					#print word.word
					if word.part != part:
						outfile.write("\n#end document\n")
						part = str(word.part)
						outfile.write("#begin document (Test); %s\n" % ("00" + str(part))[-3:])

					chain = '-'
					if word.chain:
						if i == 0 and sent.words[i+1] and not sent.words[i+1].chain:
							chain = '(' + str(word.chain) + ')'
						elif i == len(sent.words) and sent.words[i-1] and not sent.words[i-1].chain:
							chain = '(' + str(word.chain) + ')'
						elif (i > 0 and i < len(sent.words)
								   and not sent.words[i-1].chain
								   and not sent.words[i+1].chain):
							chain = '(' + str(word.chain) + ')'
						elif word.chain and i > 0 and not sent.words[i-1].chain:
							chain = '(' + str(word.chain)
						elif word.chain and i == 0:
							chain = '(' + str(word.chain)
						elif word.chain and i <= len(sent.words) and not sent.words[i+1].chain:
							chain = str(word.chain) + ')'

					#print doc.basename, word.part, str(i), word.word, chain, word.chain

					outfile.write('\t'.join([doc.basename, word.part, str(i), word.word, chain]) + '\n')
				outfile.write('\n')
			outfile.write('#end document')


	def chain(self, doc, e1, e2, chain):
		"""make sure e1 and e2 are in the same chain in the document"""

		l = []
		del_chain = None 

		if e2 and e2[0].chain:
			del_chain = e2[0].chain

		if doc.chains[chain]:
			l = doc.chains[chain]

		for e in [e1, e2]:
			if e:
				if e not in l:
					l.append(e)
					for word in e:
						word.chain = chain
		doc.chains[chain] = l
		
		if del_chain and doc.chains[del_chain]:
			del doc.chains[del_chain]
		

	def update_chain_dict(self, doc):
		for chain in doc.chains:
			for entity in doc.chains[chain]:
				for word in entity:
					if word.chain != chain:
						old_chain = word.chain
						word.chain = chain
						if doc.chains[old_chain]:
							del doc.chains[old_chain]

	def string_match(self, doc, partial=False):
		"""
		compare every entity to every other entity store matches as mapping 
		of their map number to a list each list index is the string and a 
		tuple pointing to the location of the string in the document
		{0 : ['string', (sent_num, [entity start index, end index])]}
		"""
	
		for i, e1 in enumerate(doc.entities):
			chained = True if e1[0].chain >= 0 else False
			if not chained:
				e1_words = self.resolve_entity(e1)
				if len(e1_words) == 1 and e1_words[0].lower() in self.pronouns:
					# don't work with pronouns yet
					pass
				else:
					for j, e2 in enumerate(doc.entities):
						#make sure we don't compare more than we have to
						#and we don't compare words already in a chain
						if j > i: 
							if e2[0].chain is None: 
								if e1_words == self.resolve_entity(e2):
									#e2_words = self.resolve_entity(e2)
									#print 'e1_words ' + str(e1_words)
									#print 'e2_words ' + str(e2_words)
									self.chain(doc, e1, e2, i)
									chained = True
			if not chained:
				#initializie the rest of the clusters
				self.chain(doc, e1, None, i)

	def precise_constructs(self, doc, constructs=[',','is','was']):
		for i, e1 in enumerate(doc.entities):
			e1_acronym = [word.word[0] for word in e1 if word.word[0].isupper()]
			e1_acronym = e1_acronym if len(e1_acronym) > 2 else None
			for j, e2 in enumerate(doc.entities):
				if j > i:
					if e1[0].chain is not e2[0].chain:
						# Check appositives and and Predicate Nominatives
						if self.appositive_pred_nominative(doc, e1, e2):
							self.chain(doc, e1, e2, e1[0].chain)
						# Check acronyms
						
						if e1_acronym and len(e2) > 2:
							if e1_acronym == [word.word[0] for word in e2 if word.word[0].isupper()]:
								#print [word.word for word in e1]
								#print [word.word for word in e2]
								#print 
								self.chain(doc, e1, e2, e1[0].chain)
						
		
	
	def partial_string_match(self, doc):
		for i, e1 in enumerate(doc.entities):
			e1_words = set([word.word for word in e1 if word not in self.stopwords])
			for j, e2 in enumerate(doc.entities):
				if j > i:
					if e1[0].chain is not e2[0].chain: 

						# check head matching assuming the word infinitive is the NP head
						e1_heads = set([word.infinitive for word in e1 if word.infinitive is not None])
						e2_heads = set([word.infinitive for word in e2 if word.infinitive is not None])
						if len(e1_heads.intersection(e2_heads)) > 0:
							self.chain(doc, e1, e2, e1[0].chain)

						# Check word inclusion
						if len(doc.chains[e2[0].chain]) == 1:
							if len(e2) > 1:
								if e1_words.issuperset(set(word.word for word in e2 if word not in self.stopwords)):
									self.chain(doc, e1, e2, e1[0].chain)
						
						
						
	def appositive_pred_nominative(self, doc, e1, e2, constructs=[',','is','was']):
		if e1[0].sent_num == e2[0].sent_num:
			if e2[0].index - e1[-1].index <= 2:
				sent_num = e1[0].sent_num
				start = e1[-1].index
				end = e2[0].index
				between_words = doc.sentences[sent_num].words[start : end]
				if [word.lower() for word in between_words if word in constructs]:
					return True
		return False
	

	def pronoun_resolution(self, doc):
		for sent in doc.sentences:
			#if there is a pronoun in the sentence, assume it is referring
			#to the closest entity in the sentence if there is another
			for i, entity in enumerate(sent.entities):
				if len(entity) == 1 and entity[0].word.lower() in self.pronouns:
					#TODO: add checks for pronoun gender and number
					if len(sent.entities) == 2:
						self.chain(doc, entity, sent.entities[1], entity[0].chain)
						#print [word.word for word in sent.entities[1]]
						break
					elif len(sent.entities) > 2:
						if i == 0:
							self.chain(doc, entity, sent.entities[1], entity[0].chain)
							#print [word.word for word in sent.entities[1]]
						elif i == len(sent.entities)-1:
							self.chain(doc, entity, sent.entities[i-1], entity[0].chain)
							#print [word.word for word in sent.entities[i-1]]
						else:
							prev_dist = entity[0].index - sent.entities[i-1][-1].index
							next_dist = sent.entities[i+1][0].index - entity[-1].index
							if prev_dist < next_dist:
								self.chain(doc, entity, sent.entities[i-1], entity[0].chain)
								#print [word.word for word in sent.entities[i-1]]
							else:
								self.chain(doc, entity, sent.entities[i+1], entity[0].chain)
								#print [word.word for word in sent.entities[i+1]]

					#print [word.word for word in entity]
					#print [word.word for word in sent.words]
					#print 

	def resolve_entity(self, e):
		return [word.word for word in e]

	def resolve(self):
		phases = [self.string_match, #must be run first
				  self.precise_constructs,
				  self.partial_string_match,
				  self.pronoun_resolution
				  ]

		for phase in phases:
			for doc in self.documents:
				phase(doc)
				#self.update_chain_dict(doc)
				"""
				for chain in doc.chains:
					print chain
					for entity in doc.chains[chain]:
						print [word.word for word in entity], word.sent_num, word.index, word.chain
				"""

	def concatenate_for_analysis(self, rootdir, search_term):
		response = search_term + '.response'
		gold_all = open(os.path.join(rootdir, 'all_gold'), 'w+')
		response_all = open(os.path.join(rootdir, 'all_response'), 'w+')
		for directory, subdir, files in os.walk(rootdir):
			for fi in files:
				#print 'fi' + fi
				if fi.endswith(search_term):
					print fi
					f = open(os.path.join(directory, fi))
					for line in f:
						#print line
						gold_all.write(line)
				elif fi.endswith(response):
					print fi
					f = open(os.path.join(directory, fi))
					for line in f:
						#print line
						response_all.write(line)
		print gold_all.name 
		print response_all.name
				

				
				
				

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
				path = os.path.join(directory, fi)
				f = open(path)
				basename = fi.split('/')[-1]
				cr.add_doc(f, path)
	"""
	for doc in cr.documents:
		for sentence in doc.sentences:
			print [word.word for word in sentence]
	"""

	cr.resolve()
	cr.write_output()
	cr.concatenate_for_analysis(rootdir, search_term)


















