import nltk
from nltk.corpus import conll2000

class svo_extractor:

    def __init__(self):
        train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
        self.npChunker = BigramChunker(train_sents)

    def parse(self, sentence):
        chunks = self.npChunker.parse(sentence)
        chunk = ""
        for word, pos, chunk_tag in chunks:
            np_start = False
            if chunk_tag == "B-NP":
                np_start = True
                chunk += word





class BigramChunker(nltk.ChunkParserI):
    def __init__(self, train_sents):

        train_data = [[(t, c) for w, t, c in nltk.chunk.tree2conlltags(sent)] for sent in train_sents]
        self.tagger = nltk.BigramTagger(train_data)

    def parse(self, sentence):
        tokens = nltk.pos_tag(nltk.word_tokenize(sentence))
        pos_tags = [pos for (word, pos) in tokens]
        tagged_pos_tags = self.tagger.tag(pos_tags)
        chunktags = [chunktag for (pos, chunktag) in tagged_pos_tags]
        conlltags = [(word, pos, chunktag) for ((word, pos), chunktag) in zip(tokens, chunktags)]
        return conlltags

train_sents = conll2000.chunked_sents('train.txt', chunk_types=['NP'])
npChunker = BigramChunker(train_sents)
print(npChunker.parse("I love pizza."))

import spacy
nlp = spacy.load("en_core_web_sm")
sent = "I shot an elephant"
doc=nlp(sent)

sub_toks = [(tok, tok.dep_) for tok in doc]
print(sub_toks)

print(sub_toks)