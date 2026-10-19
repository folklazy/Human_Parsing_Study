"""Seal JSON-like benchmark metadata once; avoid rehashing 10,000 contexts per score."""
import copy


def _reject(*args, **kwargs):
    raise TypeError('Frozen benchmark configuration cannot be mutated')


class FrozenDict(dict):
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _reject

    def __deepcopy__(self, memo):
        return {copy.deepcopy(k, memo): copy.deepcopy(v, memo) for k, v in self.items()}


class FrozenList(list):
    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = reverse = sort = __iadd__ = __imul__ = _reject

    def __deepcopy__(self, memo):
        return [copy.deepcopy(v, memo) for v in self]


def seal(value):
    if isinstance(value, dict):
        return FrozenDict({key: seal(item) for key, item in value.items()})
    if isinstance(value, list):
        return FrozenList(seal(item) for item in value)
    return value
