# Courtney Napoles
# <courtneyn@jhu.edu>
# 21 June 2015
# ##
# gleu.py
# 
# This script calculates the GLEU score of a sentence, as described in
# our ACL 2015 paper, Ground Truth for Grammatical Error Correction Metrics
# by Courtney Napoles, Keisuke Sakaguchi, Matt Post, and Joel Tetreault.
# 
# For instructions on how to get the GLEU score, call "compute_gleu -h"
#
# Updated 10 March 2016: fixed the denominator of the modified precision
#
# This script was adapted from bleu.py by Adam Lopez.
# <https://github.com/alopez/en600.468/blob/master/reranker/>

import math
from collections import Counter

class GLEU :

    def __init__(self,n=4) :
        self.order = 4

    def load_hypothesis_sentence(self,hypothesis) :
        self.hlen = len(hypothesis)
        self.this_h_ngrams = [ self.get_ngram_counts(hypothesis,n)
                               for n in range(1,self.order+1) ]
        
    def load_sources(self,spath) :
        self.all_s_ngrams = [ [ self.get_ngram_counts(line.split(),n)
                                for n in range(1,self.order+1) ]
                              for line in open(spath) ]
        
    def load_references(self,rpaths) :
        self.refs = [ [] for i in range(len(self.all_s_ngrams)) ]
        self.rlens = [ [] for i in range(len(self.all_s_ngrams)) ]
        for rpath in rpaths :
            for i,line in enumerate(open(rpath)) :
                self.refs[i].append(line.split())
                self.rlens[i].append(len(line.split()))

        # count number of references each n-gram appear sin
        self.all_rngrams_freq = [ Counter() for i in range(self.order) ]
        
        self.all_r_ngrams = [ ]
        for refset in self.refs :
            all_ngrams = []
            self.all_r_ngrams.append(all_ngrams)
            
            for n in range(1,self.order+1) :
                ngrams = self.get_ngram_counts(refset[0],n)
                all_ngrams.append(ngrams)
                
                for k in ngrams.keys() :
                    self.all_rngrams_freq[n-1][k]+=1
                
                for ref in refset[1:] :
                    new_ngrams = self.get_ngram_counts(ref,n)
                    for nn in new_ngrams.elements() :
                        if new_ngrams[nn] > ngrams.get(nn,0) :
                            ngrams[nn] = new_ngrams[nn]

        
    def get_ngram_counts(self,sentence,n) :
        return Counter([tuple(sentence[i:i+n])
                        for i in xrange(len(sentence)+1-n)])

    # returns ngrams in a but not in b    
    def get_ngram_diff(self,a,b) :
        diff = Counter(a)
        for k in (set(a) & set(b)) :
            del diff[k]
        return diff

    def normalization(self,ngram,n) :
        return 1.0*self.all_rngrams_freq[n-1][ngram]/len(self.rlens[0])
    
    # Collect BLEU-relevant statistics for a single hypothesis/reference pair.
    # Return value is a generator yielding:
    # (c, r, numerator1, denominator1, ... numerator4, denominator4)
    # Summing the columns across calls to this function on an entire corpus 
    # will produce a vector of statistics that can be used to compute GLEU
    def gleu_stats(self,i,version=1,r_ind=None):

      hlen = self.hlen
      rlen = self.rlens[i][0]

      # set the reference length to be the reference length closest to the
      # length of the hypothesis
      for r in self.rlens[i][1:] :
          if abs(r - hlen) < abs(rlen - hlen) :
              rlen = r
              
      yield rlen
      yield hlen

      for n in xrange(1,self.order+1):
        h_ngrams = self.this_h_ngrams[n-1]
        s_ngrams = self.all_s_ngrams[i][n-1]
        r_ngrams = self.all_r_ngrams[i][n-1]

        if version == 1 :
            r_ngrams = self.get_ngram_counts(self.refs[i][r_ind],n)

        s_ngram_diff = self.get_ngram_diff(s_ngrams,r_ngrams)
        if version >= 2 :
            s_ngram_diff = Counter()
            for k in s_ngrams :
                if k in r_ngrams :
                    s_ngram_diff[k] = max([0,s_ngrams[k]-r_ngrams[k] * \
                                           self.normalization(k,n)])

        yield max([ sum( (h_ngrams & r_ngrams).values() ) - \
                    sum( (h_ngrams & s_ngram_diff).values() ), 0 ])
        
        
        yield max([hlen+1-n, 0])

    # Compute GLEU from collected statistics obtained by call(s) to gleu_stats
    def gleu(self,stats):
       if len(filter(lambda x: x==0, stats)) > 0:
         return 0
       (c, r) = stats[:2]
       log_gleu_prec = sum([math.log(float(x)/y)
                            for x,y in zip(stats[2::2],stats[3::2])]) / 4
       return math.exp(min([0, 1-float(r)/c]) + log_gleu_prec)
