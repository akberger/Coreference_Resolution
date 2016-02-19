"""
Objects used for Coreference Resolution

Sentences are made up of Words, which are either entities or not
SyntaxTrees are searchable Sentences made up of Nodes representing Words
Documents represent a collection of sentences
"""

from collections import defaultdict

class Word(object):

	def __init__(self, s, entity_type=None, is_entity=False):
		self.word = s[3]
		self.POS = s[4]
		self.POS_phrase = s[5]
		self.infinitive = s[6] if s[6] is not '_' else None
		self.sense1 = s[7] if s[7] is not '_' else None
		self.sense2 = s[8] if s[8] is not '_' else None
		self.entity_type = None
		self.is_entity = True if is_entity else False
		#add other features

class Sentence(object):
	"""
	A list of strings, where each list item can be split into a word and
	features of that word in the format of CONLL 2012 data.
	"""

	def __init__(self, word_strings):
		self.words = self.words_from_string(word_strings) 		#list of Word objects
		self.tree = SyntaxTree(self.words)
		self.entities = []

	def words_from_string(word_strings):
		"""create Word objects from string representing a word and its features"""
		
		on_entity = 0
		on_entity_type = False
		words = []
		entity_names = defaultdict(str)
		entity_type = None

		for word in word_strings:
			word = word.split()
			#determine if word is an entity and its entity type if it has one
			on_entity += word[-1].count('(')
			if '(' in word[10]:
				entity_type = word[10][1:-1]
			else:
				entity_type = None
			words.append(Word(word, entity_type=entity_type, is_entity=on_entity))
			# keep track of the entity strings in sentence
			if on_entity:
				for i in xrange(on_entity):
					entity_names[i] += (' ' + word[3])
			else:
				for entity in entity_names: self.entities.append(entity)
				entity_name = defaultdict(str)
			# end entity and entity type if there is a closure
			on_entity -= word[-1].count(')')
			if ')' in word[10]:
				on_entity_type = False

		return words

	def make_tree(self, words):
		return SyntaxTree(words, words[0]).make_tree()

	def find_entities(self, words):
		return [word for word in words if word.is_entity]

class Document(object):

	def __init__(self, sentences):
		self.sentences = sentences
		self.entities = list()
		self.chains = {}


class Node(object):

	def __init__(self, POS, data="", parent=""):
		self.POS = POS
		self.data = data
		self.children = []
		self.parent = parent
		self.is_word = True if self.data is not None else False

	def add_child(self, child):
		self.children.append(child)


class SyntaxTree(object):

	def __init__(self, sentence):
		self.top = Node("TOP")
		self.sentence = sentence
		#self.make_tree(sentence)

	def pprint(self, indent=0, node=None):
		if not node:
			node = self.top

		print node.POS + " children: " + str([child.POS for child in node.children])
		for child in node.children:
			print 'child.POS ' + child.POS
			self.pprint(indent+1, child)

	def make_tree(self, sentence):
		cur = Node("TOP")
		for i, word in enumerate(sentence):
			print 'pprint'
			self.pprint()
			node = Node(word.POS)
			POS = word.POS_phrase.split('(')


			#print 'cur: POS ' + cur.POS + " children " + str([child.POS for child in cur.children])
			#print word.word

			for x in POS:
				print 'x ' + x
				if x == "TOP":
					#print '1 ' + x
					pass
					#do nothing
				elif ')' in x:	
					x = x.split(')')
					#print '2 ' + str(x)
					# move back up tree for each end bracket
					for end in x:
						if end == '*':
							#print '3 ' + end
							cur.add_child(node)
							#print cur.POS + " " + str([child.POS for child in cur.children])
						else: 
							#print '4 ' + end
							cur = cur.parent
				else:	
					# We are at a part of speech node
					if x == '*':
						#print '5 ' + x
						cur.add_child(node)
						#print cur.POS + " " + str([child.POS for child in cur.children])
						node.parent = cur
					elif '*' in x:
						#print '6 ' + x
						new = Node(x.replace('*', ''), parent=cur)
						cur.add_child(new)
						#print cur.POS + " " + str([child.POS for child in cur.children])
						leaf = Node(word.POS, data=word.POS, parent=new)
						cur = new
					elif x:
						print '7 ' + x
						new = Node(x, parent=cur)
						print cur.POS + ' children :' + str([child.POS for child in cur.children])
						cur.add_child(new)
						print cur.POS + ' children :' + str([child.POS for child in cur.children])
						#print cur.POS + " " + str([child.POS for child in cur.children])
						cur = new
					else:
						#do nothing
						#print '8 ' + x
						pass
						# we are probably at '', which is the first split '(' and
						# nothing should be done ex: -->(<--S(NP*  from (S(NP*
			node.parent = cur
			if cur:
				cur.add_child(node)

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

	instance = [x.split() for x in instance]
	# need to do non-trivial Word creation to track which words are entities, plus add other attributes 
	words = [Word(w[3], POS=w[4], POS_phrase=w[5]) for w in instance]
	sentence = Sentence(words)
	#print sentence.tree.top



if __name__ == '__main__':
	test()



