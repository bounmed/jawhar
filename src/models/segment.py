class Segment:
    def __init__(self, prefix, stem, suffix):
        self._prefix = prefix
        self._stem = stem
        self._suffix = suffix

    def __str__(self):
        return f"Segment(prefix={self.prefix}, stem={self.stem}, suffix={self.suffix})"

    @property
    def prefix(self):
        """Returns the prefix of the word"""
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        """Sets the prefix of the word"""
        self._prefix = value

    @property
    def stem(self):
        """Returns the stem of the word"""
        return self._stem

    @stem.setter
    def stem(self, value):
        """Sets the stem of the word"""
        self._stem = value

    @property
    def suffix(self):
        """Returns the suffix of the word"""
        return self._suffix

    @suffix.setter
    def suffix(self, value):
        """Sets the suffix of the word"""
        self._suffix = value
