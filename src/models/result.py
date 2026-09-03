"""
Result.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""
class Result:
    """
    This class provides implementations for results.
    Each result contains the voweled form, the prefix, the type of the word,
    the pattern, the root, the part of speech, the suffix, and an attribute
    indicating the priority of the result for display purposes.
    """

    def __init__(self, voweled_word, unvoweled_word, prefix, stem, lemma, word_type, word_pattern, word_root, pos, suffix, priority):
        # Class Variables
        self._voweled_word = voweled_word
        self._unvoweled_word = unvoweled_word
        self._prefix = prefix
        self._stem = stem
        self._lemma = lemma
        self._word_type = word_type
        self._word_pattern = word_pattern
        self._word_root = word_root
        self._pos = pos
        self._suffix = suffix
        self._priority = priority

    def __str__(self):
        return f"Result(voweled_word={self.voweled_word}, unvoweled_word={self.unvoweled_word}, prefix={self.prefix}, stem={self.stem}, lemma={self.lemma}, word_root={self.word_root}, word_type={self.word_type})"

    # Properties
    @property
    def voweled_word(self):
        """Returns the voweled form of the word."""
        return self._voweled_word
    @voweled_word.setter
    def voweled_word(self, value):
        """Sets the voweled form of the word"""
        self._voweled_word = value
    @property

    def unvoweled_word(self):
        """Returns the unvoweled form of the word."""
        return self._unvoweled_word
    @unvoweled_word.setter
    def unvoweled_word(self, value):
        """Sets the unvoweled form of the word"""
        self._unvoweled_word = value
    @property

    def lemma(self):
        """Returns the lemma of the word."""
        return self._lemma
    @lemma.setter
    def lemma(self, value):
        """Sets the lemma of the word"""
        self._lemma = value
    @property

    def prefix(self):
        """Returns the prefix of the word."""
        return self._prefix
    @prefix.setter
    def prefix(self, value):
        """Sets the prefix of the word"""
        self._prefix = value
    @property
    def stem(self):
        """Returns the stem of the word."""
        return self._stem
    @stem.setter
    def stem(self, value):
        """Sets the stem of the word"""
        self._stem = value
    @property
    def word_type(self):
        """Returns the type of the word."""
        return self._word_type
    @word_type.setter
    def word_type(self, value):
        """Sets the type of the word"""
        self._word_type = value
    @property
    def word_pattern(self):
        """Returns the pattern of the word."""
        return self._word_pattern
    @word_pattern.setter
    def word_pattern(self, value):
        """Sets the pattern of the word"""
        self._word_pattern = value
    @property
    def word_root(self):
        """Returns the root of the word."""
        return self._word_root
    @word_root.setter
    def word_root(self, value):
        """Sets the root of the word"""
        self._word_root = value
    @property
    def pos(self):
        """Returns the pos of the word."""
        return self._pos
    @pos.setter
    def pos(self, value):
        """Sets the pos of the word"""
        self._pos = value

    @property
    def suffix(self):
        """Returns the suffix of the word."""
        return self._suffix
    @suffix.setter
    def suffix(self, value):
        """Sets the suffix of the word"""
        self._suffix = value

    @property
    def priority(self):
        """Returns the priority of the word."""
        return self._priority
    @priority.setter
    def priority(self, value):
        """Sets the priority of the word"""
        self._priority = value
