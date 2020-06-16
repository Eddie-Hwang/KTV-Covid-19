import pickle
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from webvtt import WebVTT, Caption
from konlpy.tag import Kkma, Twitter
from tqdm import tqdm


class SubtitleWrapper:
    def __init__(self):
        self.vtt = WebVTT()

    def write_caption(self, start, end, line):
        caption = Caption(start, end, line)
        self.vtt.captions.append(caption)

    def save_caption(self, path):
        self.vtt.save('{}.vtt'.format(path))

    def read_caption(self, vtt_file):
        return WebVTT.read(vtt_file)


class Doc2Vec:
    def __init__(self):
        self.doc2vec = TfidfVectorizer()
        self.kkma = Kkma()

    def fit_doc2vec(self, doc_nouns):
        self.doc2vec.fit(doc_nouns)

    def get_nouns(self, doc):
        return self.kkma.nouns(doc)

    def get_split(self, doc):
        return doc.split(' ')
        
    def get_vec(self, doc):
        return self.doc2vec.transform([doc]).todense()

    def cos_similarity(self, vect1, vect2):
        dot_procduct = np.dot(vect1, vect2.reshape(-1,1))
        l2_norm = np.sqrt(np.sum(np.square(vect1), axis=-1)) * np.sqrt(np.sum(np.square(vect2), axis=-1))
 
        return dot_procduct / l2_norm

    def get_score(self, doc1, doc2):
        vect1 = self.get_vec(doc1)
        vect2 = self.get_vec(doc2)
        
        return self.cos_similarity(vect1, vect2)

    def get_similarity(self, doc1, doc2):
        vec1 = self.get_vec(doc1)
        vec2 = self.get_vec(doc2)

        return np.dot(vec1, vec2.T)


def load_data(path):
    print('[INFO] load from {}'.format(path))
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data

def save_data(path, data):
    with open(path, 'wb') as f:
        pickle.dump(data, f)

def get_all_doc(script_dict):
    doc = list()
    for vid_idx in script_dict:
      script  = script_dict[vid_idx]
      doc += script
    
    return doc