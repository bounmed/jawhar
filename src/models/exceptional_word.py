"""
ExceptionalWord.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class ExceptionalWord:
    """
    This class provides implementations for exceptional words.
    Each exceptional word is accompanied by its morphological analysis results.
    """

    def __init__(self, voweledform, unvoweledform, prefix, stem, type, suffix):
        # Class Variables
        self._voweledform = voweledform
        self._unvoweledform = unvoweledform
        self._prefix = prefix
        self._stem = stem
        self._type = type
        self._suffix = suffix

    # Public Methods
    @property
    def unvoweledform(self):
        """Returns the unvoweled form of the word."""
        return self._unvoweledform
    @unvoweledform.setter
    def unvoweledform(self, value):
        """Sets the unvoweled form of the word."""
        self._unvoweledform = value

    @property
    def voweledform(self):
        """Returns the voweled form of the word."""
        return self._voweledform
    @voweledform.setter
    def voweledform(self, value):
        """Sets the voweled form of the word."""
        self._voweledform = value
    
    @property
    def stem(self):
        """Returns the stem of the word."""
        return self._stem
    @stem.setter
    def stem(self, value):
        """Sets the stem of the word."""
        self._stem = value

    @property
    def type(self):
        """Returns the type of the word."""
        return self._type
    @type.setter
    def type(self, value):
        """Sets the type of the word."""
        self._type = value
    @property
    def prefix(self):
        """Returns the prefix of the word."""
        return self._prefix
    @prefix.setter
    def prefix(self, value):
        """Sets the prefix of the word."""
        self._prefix = value

    @property
    def suffix(self):
        """Returns the suffix of the word."""
        return self._suffix
    @suffix.setter
    def suffix(self, value):
        """Sets the suffix of the word."""
        self._suffix = value
