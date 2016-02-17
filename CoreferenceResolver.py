"""
Objects used for Coreference Resolution

Sentences are made up of Words, which are either entities or not
SyntaxTrees are searchable Sentences made up of Nodes representing Words
Documents represent a collection of sentences
"""

class Word(object):

	def __init__(self, word, POS=None, POS_phrase=None, infinitive=None,
				 sense=None, is_entity=False):
		self.word = word
		self.POS = POS
		self.POS_phrase = POS_phrase
		self.infinitive = infinitive
		self.sense = sense
		self.is_entity = is_entity
		#add other features


class Sentence(object):

	def __init__(self, words):
		self.words = words 		#list of Word objects
		self.tree = SyntaxTree(self.words)
		self.entities = self.find_entities(self.words)

	def make_tree(self, words):
		return SyntaxTree(words, words[0]).make_tree()

	def find_entities(self, words):
		return [word for word in words if word.is_entity]

class Document(object):

	def __init__(self, sentences):
		self.sentences = sentences
		self.entity_chains = {}


class Node(object):

	def __init__(self, POS, data="", parent=None):
		self.POS = POS
		self.data = data
		self.children = list()
		self.parent = parent
		self.is_word = True if self.data is not None else False

	def __str__(self, indent=0):
		s = "\t" * indent + self.POS + " " + self.data + "\n"
		print [child.POS for child in self.children]
		for child in self.children:
			s += child.__str__(indent+1)
		return s

	def __repr__(self):
		return '<SyntaxTree Node representation>'


class SyntaxTree(object):

	def __init__(self, sentence):
		self.top = Node("TOP")
		self.sentence = sentence
		self.make_tree(sentence)

	def make_tree(self, sentence):
		cur = Node("TOP")
		for i, word in enumerate(sentence):
			node = Node(word.POS)
			POS = word.POS_phrase.split('(')

			#print
			#print POS
			#print 'cur.POS = ' + str(cur.POS)

			for x in POS:
				if x == "TOP":
					print '1 ' + x
					continue
				elif ')' in x:	
					x = x.split(')')
					print '2 ' + str(x)
					# move back up tree for each end bracket
					for end in x:
						if end == '*':
							#print '3 ' + end
							cur.children.append(node)
							print cur.POS + " " + str([child.POS for child in cur.children])
						else: 
							#print '4 ' + end
							cur = cur.parent
				else:	
					# We are at a part of speech node
					if x == '*':
						print '5 ' + x
						cur.children.append(node)
						print cur.POS + " " + str([child.POS for child in cur.children])
						node.parent = cur
					elif '*' in x:
						print '6 ' + x
						new = Node(x.replace('*', ''), parent=cur)
						cur.children.append(new)
						print cur.POS + " " + str([child.POS for child in cur.children])
						leaf = Node(word.POS, data=word.POS, parent=new)
						cur = new
					elif x:
						print '7 ' + x
						new = Node(x, parent=cur)
						cur.children.append(new)
						print cur.POS + " " + str([child.POS for child in cur.children])
						cur = new
					else:
						#print '8 ' + x
						continue
						# we are probably at '', which is the first split '(' and
						# nothing should be done ex: -->(<--S(NP*  from (S(NP*
			node.parent = cur
			if cur:
				cur.children.append(node)

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
	print sentence.tree.top



if __name__ == '__main__':
	test()



