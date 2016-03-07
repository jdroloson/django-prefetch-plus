from _collections import defaultdict
from _collections_abc import Iterable

from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q


def do_prefetch_plus(objects, to_attr, query_set, obj_cols, qset_cols):

    items = defaultdict(lambda: [])
    if not isinstance(obj_cols, Iterable) or isinstance(obj_cols, str):
        obj_cols = (obj_cols,)
    if not isinstance(qset_cols, Iterable) or isinstance(qset_cols, str):
        qset_cols = (qset_cols,)

    sieve = Q()
    for obj in objects:
        inner_sieve = Q()
        for lhs, rhs in zip(obj_cols, qset_cols):
            levels = lhs.split(LOOKUP_SEP)
            new_obj = obj
            for level in levels[:-1]:
                new_obj = getattr(new_obj, level)
            kwargs = {rhs: getattr(new_obj, levels[-1])}
            inner_sieve &= Q(**kwargs)
        sieve |= inner_sieve
    new_query_set = query_set.filter(sieve)

    for item in new_query_set:
        vals = []
        for col in qset_cols:
            levels = col.split(LOOKUP_SEP)
            new_item = item
            for level in levels[:-1]:
                new_item = getattr(new_item, level)
            vals.append(getattr(new_item, levels[-1]))
        items[tuple(vals)].append(item)

    for obj in objects:
        vals = []
        for col in obj_cols:
            levels = col.split(LOOKUP_SEP)
            new_obj = obj
            for level in levels[:-1]:
                new_obj = getattr(new_obj, level)
            vals.append(getattr(new_obj, levels[-1]))
        setattr(obj, to_attr, items[tuple(vals)])


class PrefetchPlus(object):

    def __init__(self, to_attr, query_set, obj_cols, qset_cols):
        self.obj_cols = obj_cols
        self.to_attr = to_attr
        self.query_set = query_set
        self.qset_cols = qset_cols

    @property
    def hashable(self):
        return (
            self.to_attr,
            str(self.query_set.query),
            self.obj_cols,
            self.qset_cols
        )

    def __eq__(self, other):
        if isinstance(other, PrefetchPlus):
            return self.hashable == other.hashable
        return False

    def __hash__(self):
        return hash(self.__class__) ^ hash(self.hashable)


class PrefetchPlusQuerySet(QuerySet):

    def __init__(self, *args, **kwargs):
        super(PrefetchPlusQuerySet, self).__init__(*args, **kwargs)
        self._prefetch_plus_related_lookups = []
        self._prefetch_plus_done = False

    def prefetch_plus(self, to_attr, query_set, obj_cols, qset_cols):
        clone = self._clone()
        clone._prefetch_plus_related_lookups.append(
            PrefetchPlus(to_attr, query_set, obj_cols, qset_cols)
        )
        return clone

    def _prefetch_plus_related_objects(self):
        # This method can only be called once the result cache has been filled.
        for pre_plus in self._prefetch_plus_related_lookups:
            do_prefetch_plus(
                self._result_cache,
                pre_plus.to_attr,
                pre_plus.query_set,
                pre_plus.obj_cols,
                pre_plus.qset_cols
            )
        self._prefetch_done = True

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(PrefetchPlusQuerySet, self)._clone(
            klass=klass,
            setup=setup,
            **kwargs
        )
        c._prefetch_plus_related_lookups = \
            self._prefetch_plus_related_lookups[:]
        return c

    def _fetch_all(self):
        super(PrefetchPlusQuerySet, self)._fetch_all()
        if (self._prefetch_plus_related_lookups and
                not self._prefetch_plus_done):
            self._prefetch_plus_related_objects()
