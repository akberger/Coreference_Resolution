import re
import string
from collections import OrderedDict
from nltk.tree import Tree
from copy import deepcopy

def make_data_dict(infile, make_trees=True):
    """Returns a dictionary of the sentences in `infile`.

    If `make_trees` is true, create an NLTK Tree for each sentence and store it
    in data_dict[sent_num]['tree']

    data_dict[0] will be the first sentence in the file.
    data_dict[0][0] will be the dictionary of features for the first word in the
    first sentence of the file.
    """
    data_dict = OrderedDict()
    sents = []
    cur_sent = []
    with open(infile) as inf:
        for line in inf:
            if line != '\n' and not line.startswith('#'):
                cur_sent.append(line)
            else:
                if cur_sent:
                    sents.append(cur_sent)
                    cur_sent = []
                else:
                    continue

    for i,sent in enumerate(sents):
        sent_tokens = []
        sent_dict = OrderedDict()
        for line in sent:
            line_dict = {}
            cols = line.split()
            n_word = int(cols[2])
            word = cols[3]
            pos = cols[4]
            tree = cols[5]
            e_type = cols[10]
            coref = cols[-1]
            line_dict['word'] = word
            line_dict['pos'] = pos
            line_dict['tree'] = tree
            line_dict['e_type'] = e_type
            line_dict['coref'] = coref
            sent_tokens.append(word)
            sent_dict[n_word] = line_dict
        sent_dict['tokens'] = sent_tokens
        data_dict[i] = sent_dict

    if make_trees:
        for n, d1 in data_dict.iteritems():
            tree = ""
            for w, d2 in d1.iteritems():
                if w != 'tokens':
                    tree += d2['tree'].replace('*', '({} {})'.format(
                        d2['pos'], d2['word']))
            data_dict[n]['tree'] = Tree.fromstring(tree)

    return data_dict

def get_corefs(data_dict):
    """ Given a data_dict create by `make_data_dict`, return a list of mentions
    (s, i, j, c), where s is the sentence number, c is the chain number, i is
    the first word index of the mention, and j is the last word index of the
    mention.
    """
    p1 = re.compile(r'\(\d+\)') # single line contains whole mention
    p2 = re.compile('\(\d+\|*(?!\))') # starting (nested) mentions, e.g., (0|(3
    p3 = re.compile(r'(?<!\()\d+\)\|*') # ending (nested) mentions, e.g., 8)|6)
    mentions = []
    for k,v in data_dict.iteritems(): # k is sent num
        sent = k
        start = []
        end = []
        for subk, subv in v.items(): # subk is word num
            if subk == 'tree' or subk == 'tokens': # ignore sentence-level trees
                continue
            # print ('sent:',sent,'word:',subk,'coref:',subv['coref'],
            #       'start:',start,'end:',end)
            start_match = re.findall(p2, subv['coref'])
            end_match = re.findall(p3, subv['coref'])
            if re.match(p1, subv['coref']):
                # full match e.g., (0)
                mentions.append((sent, subk, subk,
                                 extract_digit(subv['coref'])))
            elif len(start_match) != 0:
                # handle (0|(3|(5)
                sub_full_match = re.findall(p1, subv['coref'])
                if sub_full_match:
                    for m in sub_full_match:
                        mentions.append((sent, subk, subk, extract_digit(m)))
                for m in start_match:
                    start.append((extract_digit(m), subk))
            elif len(end_match) != 0:
                # handle 0)|3)|(5)
                sub_full_match = re.findall(p1, subv['coref'])
                for m in sub_full_match:
                    mentions.append((sent, subk, subk, extract_digit(m)))
                ends = [(extract_digit(m), subk) for m in end_match]
                for e in ends:
                    if e[0] == start[-1][0]:
                        mentions.append((sent, start.pop(), e))
                    else:
                        for s in start:
                            if e[0] == s[0]:
                                mentions.append((sent, s, e))
                                start.remove(s)
        # reformat mentions to be uniform
        for m in mentions:
            if isinstance(m[1], tuple):
                new_m = (m[0], m[1][1], m[2][1], m[1][0])
                mentions[mentions.index(m)] = new_m
    return sorted(mentions, key=lambda x: (x[0], x[1], x[2]))

# Don't use this
def get_all_mentions(data_dict, corefs):
    """ Get all the NPs from the document.

    We don't actually need this since the coref spans in the data
    designate mentions. Also, some mentions could be NPs.
    """
    # return (n_sent, start, end, coref) # if not coreferent, None
    mentions = []
    nps = [] # (n_sent, np_tree) tuples
    for outer_k, outer_v in data_dict.iteritems():
        for inner_k, inner_v in outer_v.iteritems():
            if inner_k == 'tree':
                trees = list(inner_v.subtrees(filter=lambda x: x.label() == 'NP'))
                nps.extend([(outer_k, t) for t in trees])
    for np in nps:
        n_sent = np[0]
        np_tokens = np[1].leaves()
        sent_tokens = data_dict[n_sent]['tokens']
        start = sent_tokens.index(np_tokens[0])
        end = sent_tokens.index(np_tokens[-1])
        # determine anaphoricity
        coref = False
        for c in corefs:
            if (n_sent, start, end) == c[:3]:
                mentions.append((n_sent, start, end, c[-1]))
                coref = True
        if not coref:
            mentions.append((n_sent, start, end, None))
    mentions = list(set(mentions))
    return sorted(mentions, key=lambda x: (x[0], x[1], x[2]))

def make_mention_dict(mention, data_dict):
    """Given a 4-tuple created by `read_data.get_corefs` or
    `read_data.get_all_mentions, return a featurizable dict."""
    m_dict = {}
    m_sent_num = mention[0]
    m_chain = mention[3]
    m_string = ""
    m_e_type = ""
    m_pos = ""
    for i in range(mention[1], mention[2]+1):
        m_string += data_dict[m_sent_num][i]['word'] + ' '
        m_pos += data_dict[m_sent_num][i]['pos'] + ' '
        m_e_type += data_dict[m_sent_num][i]['e_type']
    m_dict = {
        'sent_num': m_sent_num,
        'start': mention[1],
        'end': mention[2],
        'string': m_string.strip(),
        'e_type': m_e_type.replace('(','').replace('*','').replace(')',''),
        'pos': m_pos,
        'chain': m_chain,
        'tree': data_dict[m_sent_num]['tree']}
    return m_dict

def pprint_dict(d):
    import json
    print json.dumps(d, indent=4)

def extract_digit(string):
    return int(''.join([c for c in string if c.isdigit()]))

