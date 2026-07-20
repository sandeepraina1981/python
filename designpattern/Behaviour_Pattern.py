from collections.abc import Iterable

class ElementList:
    def __init__(self, elements):
        if not isinstance(elements, Iterable):
            raise TypeError("Elements must be an Iterable")

        self._data = list(elements)

    def append(self, value):
        self._data.append(value)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f"ElementList({self._data})"

    def _as_elementlist(self, other):
        if isinstance(other, ElementList):
            return other

        if isinstance(other, (list, tuple)):
            return ElementList(other)

        return None

    def __add__(self, other):
        other = self._as_elementlist(other)

        if other:
            if len(self) != len(other):
                raise ValueError("Length mismatch")

            return ElementList(a + b for a, b in zip(self, other))

        return NotImplemented

    def __sub__(self, other):
        other = self._as_elementlist(other)

        if other:
            if len(self) != len(other):
                raise ValueError("Length mismatch")

            return ElementList(a - b for a, b in zip(self, other))

        return NotImplemented

    def __mul__(self, other):
        other = self._as_elementlist(other)

        if other:
            if len(self) != len(other):
                raise ValueError("Length mismatch")

            return ElementList(a * b for a, b in zip(self, other))

        return NotImplemented


if __name__ == "__main__":
    a = [1,2,3]
    b = [4,5,6]
    print(ElementList([1,2,3]) * a - ElementList([4,5,6]))
    print(a + b)


