"""
Objects used for Coreference Resolution

Sentences are made up of Words, which are either entities or not
SyntaxTrees are searchable Sentences made up of Nodes representing Words
Documents represent a collection of sentences
"""

from collections import defaultdict
from nltk.tree import *

class Word(object):

	def __init__(self, s, index, sent_num, entity_type=None, is_entity=False):
		self.index = index
		self.part = s[1]
		self.word = s[3]
		self.POS = s[4]
		self.POS_phrase = s[5]
		self.infinitive = s[6] if s[6] is not '-' else None
		self.sense1 = s[7] if s[7] is not '-' else None
		self.sense2 = s[8] if s[8] is not '-' else None
		self.entity_type = None
		self.is_entity = True if is_entity else False
		self.chain = None
		self.sent_num = sent_num

class Sentence(object):
	"""
	A list of strings, where each list item can be split into a word and
	features of that word in the format of CONLL 2012 data.
	"""

	def __init__(self, word_strings, sent_num):
		self.sent_num = sent_num
		#words - Word objects for each word in the sentence
		#entities - list of lists of Word objects. Each index corresponds to an entity
		self.words, self.entities = self.words_from_string(word_strings) 
		#self.tree = self.make_tree(word_strings)
		

	def words_from_string(self, word_strings):
		"""create Word objects from string representing a word and its features

		Uncommenting the comment blocks in this method would allow for every entity to
		be captured, which means that nested entities would be captured, not just
		the largest entity part of a nested entity. I did not have time, however, to 
		figure out how to address these nested entities in chaining and the output.
		"""

		words = []
		on_entity = 0 # track how many entities are currently being processes
		entities = []
		"""current_entities = defaultdict(list)"""
		current_entity = []
		entity_type = None

		for i, word in enumerate(word_strings):
			word = word.split()
			#determine if word is an entity and its entity type if it has one
			on_entity += word[-1].count('(')
			if '(' in word[10]:
				entity_type = word[10][1:-1]
			new_word = Word(word, i, self.sent_num, entity_type=entity_type, is_entity=on_entity)
			words.append(new_word)
			
			# keep track of the entity strings in sentence and touple it with its
			#location in the sentence for indexing later
			if on_entity:
				"""
				for j in xrange(on_entity):
					current_entities[j].append(new_word)
				"""
				current_entity.append(new_word)
			else:
				"""
				for entity in current_entities:
					entities.append(current_entities[entity])
				current_entities = defaultdict(list)
				"""
				if current_entity:
					entities.append(current_entity)
					current_entity = []

			# end entity and entity type if there is a closure
			on_entity -= word[-1].count(')')
			if ')' in word[10]:
				entity_type = None

		return words, entities

	def resolve_entity(self, entity):
		"""
		entity comes in as a list of tuples(word, word_index)
		return the string of all words and the first and last index
		"""

		string = ' '.join([word for word, index in entity])
		indices = [entity[0][1], entity[-1][1]]

		return string, indices	

	def make_tree(self, word_strings):
		"""make nltk tree object from the sentence"""

		POS_envs = []
		for i,word in enumerate(word_strings):
			word = word.split()
			env = word[5]
			POS_envs.append(env)

		s = ''.join(POS_envs).replace('*', '')

		return Tree.fromstring(s)

	def old_make_tree(self, words):
		return SyntaxTree(words, words[0]).make_tree()

	def old_find_entities(self, words):
		return [word for word in words if word.is_entity]

class Document(object):

	def __init__(self, document, basename):
		self.sentences = self.make_sentences(document)
		#make a flat list of all entities in the document so each index is a 
		#list corresponding to an entity
		self.entities = self.flatten_entities(self.sentences)
		self.chains = defaultdict(list)
		self.basename = basename

	def make_sentences(self, f):
		"""make a document from a CONLL file"""

		document_sentences = []
		sentence = []
		sent_num = 0

		for i, line in enumerate(f):
			if not line.startswith('#'):
				if line.split():
					sentence.append(line)
				else:
					document_sentences.append(Sentence(sentence, sent_num))
					sentence = []
					sent_num += 1

		return document_sentences

	def flatten_entities(self, sentences):
		entities = []
		for s in sentences:
			for i in s.entities:
				entities.append(i)

		return entities


def test():
	instance = ['bc/cctv/00/cctv_0000   0    0         With     IN  (TOP(S(PP*           -    -   -   Speaker#1       *             *   (ARGM-MNR*        *      -',
				'bc/cctv/00/cctv_0000   0    1        their   PRP$        (NP*           -    -   -   Speaker#1       *             *            *        *    (18)',
				'bc/cctv/00/cctv_0000   0    2       unique     JJ           *           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0    3        charm     NN          *))       charm   -   -   Speaker#1       *             *            *)       *      -',
				'bc/cctv/00/cctv_0000   0    4            ,      ,           *           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0    5        these     DT        (NP*           -    -   -   Speaker#1       *             *       (ARG0*        *    (18',
				'bc/cctv/00/cctv_0000   0    6         well     RB      (ADJP*           -    -   -   Speaker#1       *    (ARGM-EXT*)           *        *      -',
				'bc/cctv/00/cctv_0000   0    7           -    HYPH           *           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0    8        known    VBN           *)        know  01   2   Speaker#1       *           (V*)           *        *      -',
				'bc/cctv/00/cctv_0000   0    9      cartoon     NN           *           -    -   -   Speaker#1       *        (ARG1*)           *        *      -',
				'bc/cctv/00/cctv_0000   0   10       images    NNS           *)       image   -   2   Speaker#1       *      (C-ARG1*)           *)       *     18)',
				'bc/cctv/00/cctv_0000   0   11         once     RB      (ADVP*           -    -   -   Speaker#1       *             *   (ARGM-TMP*        *      -',
				'bc/cctv/00/cctv_0000   0   12        again     RB           *)          -    -   -   Speaker#1       *             *            *)       *      -',
				'bc/cctv/00/cctv_0000   0   13       caused    VBD        (VP*        cause  01   1   Speaker#1       *             *          (V*)       *      -',
				'bc/cctv/00/cctv_0000   0   14         Hong    NNP      (S(NP*           -    -   -   Speaker#1   (GPE*             *            *   (ARG1*    (23',
				'bc/cctv/00/cctv_0000   0   15         Kong    NNP           *)          -    -   -   Speaker#1       *)            *            *        *)    23)',
				'bc/cctv/00/cctv_0000   0   16           to     TO        (VP*           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0   17           be     VB        (VP*           be  01   1   Speaker#1       *             *            *      (V*)     -',
				'bc/cctv/00/cctv_0000   0   18            a     DT     (NP(NP*           -    -   -   Speaker#1       *             *            *   (ARG2*      -',
				'bc/cctv/00/cctv_0000   0   19        focus     NN           *)       focus   -   1   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0   20           of     IN        (PP*           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0   21    worldwide     JJ        (NP*           -    -   -   Speaker#1       *             *            *        *      -',
				'bc/cctv/00/cctv_0000   0   22    attention     NN     *)))))))   attention   -   3   Speaker#1       *             *            *        *)     -',
				'bc/cctv/00/cctv_0000   0   23            .      .          *))          -    -   -   Speaker#1       *             *            *        *      -',]
	"""
	d = Document(instance)
	print d.entities
	for s in d.sentences:
		print s.entities
		print s.tree
	"""
	S = Sentence(instance, 0)
	print S.entities
	print S.tree



if __name__ == '__main__':
	test()
