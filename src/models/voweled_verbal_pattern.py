"""
VoweledVerbalPattern.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class VoweledVerbalPattern:
    """
    This class provides implementations for voweled verbal patterns. Each pattern is characterized by its id, voweled form, canonical form of the pattern,
    the type of the pattern, the augmentation of the pattern, the case of the word,
    an attribute indicating the tense, number, gender and the mood of the pattern,and the transitivity of the pattern.
    """

    def __init__(self, id, diac, canonic, type, aug, cas, ncg, trans):
        # Class Variables
        self._id = id
        self._diac = diac
        self._canonic = canonic
        self._type = type
        self._aug = aug
        self._cas = cas
        self._ncg = ncg
        self._trans = trans

    
    # Properties
    @property
    def id(self):
        """Returns the identifiant of the pattern."""
        return self._id
    @property
    def diac(self):
        """Returns the voweled form of the pattern."""
        return self._diac
    @property
    def canonic(self):
        """Returns the canonical of the pattern."""
        return self._canonic
    @property
    def type(self):
        """Returns the type of the pattern."""
        return self._type
    @property
    def aug(self):
        """Returns the augmentation of the pattern."""
        return self._aug
    @property
    def cas(self):
        """Returns the case of the pattern."""
        return self._cas
    @property
    def ncg(self):
        """Returns the tense, number, gender and the mood of the pattern."""
        return self._ncg
    @property
    def trans(self):
        """Returns the transitivity of the pattern."""
        return self._trans
    @property
    def trans(self):
        """Returns the transitivity of the pattern."""
        return self._trans

    @id.setter
    def id(self, value):
        """Sets the identifiant of the pattern."""
        self._id = value
    @diac.setter
    def diac(self, value):
        """Sets the voweled form of the pattern."""
        self._diac = value
    @canonic.setter
    def canonic(self, value):
        """Sets the canonical form of the pattern."""
        self._canonic = value
    @type.setter
    def type(self, value):
        """Sets the type of the pattern."""
        self._type = value
    @aug.setter
    def aug(self, value):
        """Sets the augmentation of the pattern."""
        self._aug = value
    @cas.setter
    def cas(self, value):
        """Sets the case of the pattern."""
        self._cas = value
    @ncg.setter
    def ncg(self, value):
        """Sets the tense, number, gender and the mood of the pattern."""
        self._ncg = value
    @trans.setter
    def trans(self, value):
        """Sets the transitivity of the pattern."""
        self._trans = value
