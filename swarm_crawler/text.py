BREADABILITY_AVAILABLE = True
try:
    from breadability.readable import Article, prep_article, check_siblings
except ImportError:
    BREADABILITY_AVAILABLE = False
    Article = object


from operator import attrgetter
from werkzeug.utils import cached_property

import re

from lxml.etree import tounicode, tostring


class PageText(Article):
    WHITESPACE = {' ':re.compile(r"[\s\r\n]+"),
                  '':re.compile(r"\.{3,}"),}
    CANDIDATE_SEPARATOR = u'\r\n'
    def __init__(self, *args, **kwargs):
        if not BREADABILITY_AVAILABLE:
            raise ImportError('breadability is not available')
        super(PageText, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.winner()

    def stripped(self, text):
        for replacement, whitespace in self.WHITESPACE.items():
            text = re.sub(whitespace, replacement, text)
        return text

    def slice(self, before=1, reverse=True):
        if self.candidates:
            # cleanup by removing the should_drop we spotted.
            [n.drop_tree() for n in self._should_drop
                if n.getparent() is not None]

            # right now we return the highest scoring candidate content
            by_score = sorted([c for c in self.candidates.values()],
                key=attrgetter('content_score'), reverse=reverse)

            # since we have several candidates, check the winner's siblings
            # for extra content

            for winner in by_score[:before]:
                winner = check_siblings(winner, self.candidates)

                # updated_winner.node = prep_article(updated_winner.node)
                if winner.node is not None:
                    yield winner.node

    def winner(self, greed=1):
        if not self.candidates:
            return u''

        if isinstance(greed, float):
            if 0 > greed > 1.0:
                raise ValueError('greed coeft should be integer or 0<x<1.0')
            greed = int(round(len(self.candidates)*greed))


        return self.CANDIDATE_SEPARATOR.join((self.stripped(tounicode(node,
                         method='text')) for node in self.slice(before=greed)))