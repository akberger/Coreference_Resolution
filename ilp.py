import os
import glob
import numpy as np
import nltk.tree
import cPickle
from tqdm import tqdm
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction import DictVectorizer
from pulp import *

from read_data import make_data_dict, make_mention_dict
from read_data import get_corefs, get_all_mentions

data_dir = '../data/train'

PRONOUNS = ['i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'myself',
            'yourself', 'himself', 'herself', 'ourselves',
            'themselves']

def make_train_instances(data_dir):
    """
    Training instances are constructed using pairs (i, j) where
    j is an anaphor and i is a candidate antecedent. Each pair
    is labeled either 1 for coreferent, else 0. Only immediately
    adjacent pairs in a coreference chain are used to generate
    positive examples. The first NP in the pair is the antecedent,
    and the second is the anaphor. Negative examples are formed by
    pairing each mention in between i and j that is either not
    coreferent with j.

    """
    train_files = glob.glob(data_dir+'/*.v4_auto_conll')
    dataset = []
    for train_file in tqdm(train_files):
        file_instances = [os.path.basename(train_file)]
        d = make_data_dict(train_file)
        c = get_corefs(d)
        # m = get_all_mentions(d, c)
        rev_c = c[::-1] # reverse c to start from end of document
        for idx, j in enumerate(rev_c):
            for i in rev_c[idx+1:]:
                if i[-1] == j[-1]: # match
                    file_instances.append((i, j, True))
                    break
                else:
                    file_instances.append((i, j, False))
        dataset.append(file_instances)
    return dataset

def make_dataset(training_samples):
    """Make dataset usable by sklearn."""
    # X: array (n_features, n_samples)
    # y: array (n_samples,), 1 if coreferent
    X = []
    y = []
    for doc_instances in tqdm(training_samples):
        filename = doc_instances[0]
        d = make_data_dict(os.path.join(data_dir, filename))
        for pair in doc_instances[1:]:
            i = pair[0]
            j = pair[1]
            label = 1 if pair[2] else 0
            m_i = make_mention_dict(i, d)
            m_j = make_mention_dict(j, d)
            feat_dict = featurize(m_i, m_j, d)
            X.append(feat_dict)
            y.append(label)
    print "Vectorizing feature dicts..."
    v = DictVectorizer(sparse=False)
    X = v.fit_transform(X)
    print "One hot encoding..."
    enc = OneHotEncoder()
    X = enc.fit_transform(X).toarray()
    y = np.array(y)
    dataset = (X, y)
    with open('dataset.pkl', 'w') as p:
        cPickle.dump(dataset, p)
    return X, y, v, enc

def build_model(X, y):
    # find optimal regularization strength
    cs = [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
    lr_cv = LogisticRegressionCV(Cs=cs, solver='liblinear')
    lr_vc.fit(X, y)
    # train pairwise maxent coref classifier
    lr = LogisticRegression(C=lr_cv.C_, random_state=0)
    return lr

def test(model, test_doc, vectorizer= None, encoder=None,
         first_match=True, ilp=False):
    # for each mention, work backwards and add a link for all previous
    # which the clasifier deems coreferent (first_match=False)
    #
    # for each mention, work backwards until you find a previous mention
    # which the classifier thinks is coreferent, add a link, and terminate
    # the search (first_match=True)
    d = make_data_dict(test_doc)
    c = get_corefs(d)
    links = []
    rev_c = c[::-1]
    if ilp:
        rev_c_idx = [(i,m) for i,m in enumerate(re_v)]
        m2 = [(m_i, m_j) for m_i in rev_c_idx for m_j in rev_c_idx]
        m2 = sorted(m2, key=lambda x: (x[0][0], x[1][0]), reverse=True)
        m_idx = {i,j: fm for (i[0], j[0]) in m2 for fm in
                 full_featurize(i[1], j[1], d, v, enc) for (i,j) in m2}

        prob = LpProblem('coref', LpMaximize)
        i = LpVariable('i', lowBound=0, cat=Integer) # m_i index
        j = LpVariable('j', lowBound=0, cat=Integer) # m_j index
        p = model.predict_log_proba(full_featurize(m2))
        x = model.predict(full_featurize(m2))

    else:
        for idx, j in enumerate(rev_c):
            for i in rev_c[idx+1:]:
                X = featurize(make_mention_dict(i, d),
                              make_mention_dict(j, d), d)
                ypred = model.predict(X)
                if ypred == 1:
                    links.append((i,j))
                    if first_match:
                        break
                    else:
                        continue
    return links

def full_featurize(m2, v, enc):
    X = []
    m_i = make_mention_dict(i, d)
    m_j = make_mention_dict(j, d)
    feat_dict = featurize(m_i, m_j, d)
    X.append(feat_dict)
    X = v.fit_transform(X)
    enc = OneHotEncoder()
    X = enc.fit_transform(X).toarray()
    return X

def write_test_output(links, test_doc, outfile):
    with open(test_doc) as doc, open(outfile) as output:
        for line in doc:
            if line.startswith('#'):
                continue
            elif line == '\n':
                output.write('\n')
            else:
                filename = line.split()[0]
                # insert coref if link here


def featurize(m_i, m_j, data_dict):
    """ `m_i` is candidate antecedent, `m_j` is anaphor,
    represented as mention_dict objects."""
    fdict = {
        'str_match': strmatch(m_i['string'], m_j['string']),
        'type_match': type_match(m_i, m_j),
        'dist': abs(m_j['sent_num'] - m_i['sent_num']),
        'i_pron': 1 if m_i['string'].lower() in PRONOUNS else 0,
        'j_pron': 1 if m_j['string'].lower() in PRONOUNS else 0,
        'i_n_words': len(m_i['string'].split()),
        'j_n_words': len(m_j['string'].split()),
        'both_proper': check_both_proper(m_i,m_j),
        'subject_i': is_subject(m_i, data_dict),
        'defnp': def_np(m_j),
        'demnp': dem_np(m_j),
        'i_gender': gender(m_i),
        'j_gender': gender(m_j),
        'gender_agree': gender_agr(m_i, m_j),
        #'appositive': appositive(m_j),
        'embedded': embedded(m_i, m_j),
        'num_agr': num_agr(m_i, m_j)
    }
    return fdict

def type_match(m_i, m_j):
    if m_i['e_type'] and m_j['e_type']:
        if m_i['e_type'] == m_j['e_type']:
            return 1
    return 0

def def_np(m_j):
    return 1 if m_j['string'].lower().split()[0] == 'the' else 0

def dem_np(m_j):
    dems = ['this', 'that', 'these', 'those']
    return 1 if m_j['string'].lower().split()[0] in dems else 0

def strmatch(s1, s2):
    if truncate_str(s1) == truncate_str(s2):
        return 1
    else:
        return 0

def truncate_str(string):
    dets = ['a', 'an', 'the', 'this', 'these', 'those', 'that']
    if string.split()[0] in dets:
        return ' '.join(string.split()[1:])
    return string

def check_both_proper(m_i, m_j):
    m_i_toks = m_i['string'].split()
    m_j_toks = m_j['string'].split()
    for t in m_i_toks:
        if not t[0].isupper() or not t[1:].islower():
            return 0
    for t in m_j_toks:
        if not t[0].isupper() or not t[1:].islower():
            return 0
    return 1

def is_subject(m_i, d):
    subj = find_subject(m_i['tree'])
    if subj:
        if subj.leaves() == m_i['string'].split():
            return 1
    return 0

def find_subject(tree):
    if isinstance(tree,nltk.Tree):
        if tree.label() == 'TOP':
            return find_subject(tree.copy().pop())
        elif tree.label() == 'S':
            try:
                if 'NP' in tree[0].label() and 'VP' in tree[1].label():
                    return tree[0]
            except IndexError:
                return 0

def gender_agr(m_i, m_j):
    if gender(m_i) == gender(m_j) and gender(m_i) != 'unk':
        return 1
    else:
        return 0

def gender(m):
    feminine = ['she', 'her', 'miss', 'mrs.', 'ms.', 'lady',
                'woman', 'girl', 'ma\'am']
    masculine = ['he', 'his', 'mr.', 'sir', 'man', 'boy']
    if any(s in feminine for s in m['string'].split()):
        return 'fem'
    elif any(s in masculine for s in m['string'].split()):
        return 'masc'
    else:
        return 'unk'

def appositive(m_j):
    tokens = m_j['string'].split()
    a = list(t.subtrees(filter=lambda x:
                    (x.label() == 'NP' and len(x) == 3 and x[0].label() == 'NP'
                     and x[1].label() == ',' and x[2].label() == 'NP')))
    return 1 if a else 0

def number(m):
    toks = m['string'].split()
    pos_list = m['pos'].split()
    for pos in ['NN', 'NNS', 'NNP', 'NNPS', 'PRP', 'PRP$']:
        if pos in pos_list:
            if pos.endswith('S'):
                return 'plural'
    return 'singular'

def num_agr(m_i, m_j):
    if number(m_i) == number(m_j):
        return 1
    else:
        return 0

def embedded(m_i, m_j):
    m_i_sent = m_i['sent_num']
    m_j_sent = m_j['sent_num']
    m_i_start = m_i['start']
    m_j_start = m_j['start']
    m_i_end = m_i['end']
    m_j_end = m_j['end']
    if m_i_sent == m_j_sent:
        x = [(m_i_start, 's'), (m_i_end, 'e'), (m_j_start, 's'), (m_j_end, 'e')]
        x = sorted(x, key=lambda x: (x[0], x[1]))
        num_intervals = 0
        for i in x:
            if i[1] == 's':
                num_intervals += 1
                if num_intervals > 1:
                    return 1
            else:
                num_intervals -= 1
    return 0
