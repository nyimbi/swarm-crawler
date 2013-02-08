from itertools import permutations
from datrie import Trie
if __name__ == '__main__':
    # trie = Trie()

    for f,t in permutations(['subject', 'predicate', 'object'], 2):
        print '%s->%s'%(f,t)