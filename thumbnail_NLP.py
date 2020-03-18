import spacy,nltk
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag



doc = "AskReddit asks: what is the worst thing you can type into google?"



def preprocess(sent):
    sent = nltk.word_tokenize(sent)
    sent = nltk.pos_tag(sent)
    return sent

sent = preprocess(doc)

pattern = 'NP: {<DT>?<JJ>*<NN>}'

cp = nltk.RegexpParser(pattern)
cs = cp.parse(sent)
print(cs)


from nltk.chunk import conlltags2tree, tree2conlltags,ne_chunk
from pprint import pprint
iob_tagged = tree2conlltags(cs)
pprint(iob_tagged)

ne_tree = ne_chunk(pos_tag(word_tokenize(doc)))
print(ne_tree)


import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()


pprint([(X.text, X.label_) for X in doc.ents])

pprint([(X, X.ent_iob_, X.ent_type_) for X in doc])
