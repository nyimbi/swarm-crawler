from datrie import Trie, State, Iterator
class State(State):
    def __unicode__(self):
        return u"term:%s, leaf:%s, single: %s" % (
            self.is_terminal(),
            self.is_leaf(),
            self.is_single(),
        )

class TrieTree(Trie):
    """Unordered tree"""
    def suffixes(self, prefix):
        state = State(self)
        state.walk(prefix)
        it = Iterator(state)
        while it.next():
            key = it.key()
            if key:
                yield key

    def leafs(self, prefix):
        for suffix in self.suffixes(prefix):
            key = prefix + suffix

            state = State(self)
            state.walk(key)
            # after deletion state not changed
            # if state.is_single():
            #     yield key
            # so we are testing leaf with other method
            if not any(self.suffixes(key)):
                yield key

    def children(self, parent=u''):
        if not isinstance(parent, unicode):
            parent = unicode(parent)
        keys = []
        l = len(parent)
        for leaf in self.leafs(parent):
            # print '>',leaf
            key = min((p for p in self.iter_prefixes(leaf) if len(p)>l),
                      key=len)
            if key and not key in keys:
                keys.append(key)
        return keys

    def traverse(self, parent=u'', depth=0):
        for k in self.children(parent):
            yield depth, k, self[k]
            for item in self.traverse(k, depth+1):
                yield item

    def pformat(self, parent=u'', depth=0, indent='\t', format='%s: %s\n'):
        for depth, key, value in self.traverse(parent, depth):
            yield indent*depth + format%(key, value)
            
    def pprint(self, parent=u'', depth=0, indent='\t', format='%s: %s\n'):
        for s in self.pformat(parent, depth, indent, format):
            print s,