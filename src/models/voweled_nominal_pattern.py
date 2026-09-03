"""
VoweledNominalPattern.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""


class VoweledNominalPattern:
    """
    This class provides implementations for voweled nominal patterns.
    Each pattern is characterized by its ID, voweled form, canonical form of the pattern,
    the type of the pattern, the case of the word, and an attribute indicating
    the number, gender, and the definiteness of the pattern.
    """

    def __init__(self, id, diac, canonic, type, cas, ncg):
        # Class Variables
        self._id = id       # The identifier of the pattern
        self._diac = diac     # The voweled form of the pattern
        self._canonic = canonic  # The canonical form of the pattern
        self._type = type     # The type of the pattern
        self._cas = cas      # The case of the pattern
        self._ncg = ncg      # Indicates the number, gender, and definiteness of the pattern

    def __str__(self) -> str:
        return f"VoweledNominalPattern(id={self.id}, diac={self.diac}, canonic={self.canonic}, type={self.type})"

    # Properties
    @property
    def id(self):
        """Returns the identifier of the pattern"""
        return self._id

    @id.setter
    def id(self, value):
        """Sets the identifier of the pattern"""
        self._id = value

    @property
    def diac(self):
        """Returns the voweled form of the pattern"""
        return self._diac

    @diac.setter
    def diac(self, value):
        """Sets the voweled form of the pattern"""
        self._diac = value

    @property
    def canonic(self):
        """Returns the canonical form of the pattern"""
        return self._canonic

    @canonic.setter
    def canonic(self, value):
        """Sets the canonical form of the pattern"""
        self._canonic = value

    @property
    def type(self):
        """Returns the type of the pattern"""
        return self._type

    @type.setter
    def type(self, value):
        """Sets the type of the pattern"""
        self._type = value

    @property
    def cas(self):
        """Returns the case of the pattern"""
        return self._cas

    @cas.setter
    def cas(self, value):
        """Sets the case of the pattern"""
        self._cas = value

    @property
    def ncg(self):
        """Returns the number, gender, and definiteness of the pattern"""
        return self._ncg

    @ncg.setter
    def ncg(self, value):
        """Sets the number, gender, and definiteness of the pattern"""
        self._ncg = value
