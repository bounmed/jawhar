"""
ProperNoun.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class ProperNoun:
    """
    This class provides implementations for Arabic proper nouns.
    Each proper noun is characterized by its unvoweled form, voweled form, and type.
    """

    def __init__(self, unvoweledform, voweledform, type):
        # Class Variables
        self._unvoweledform = unvoweledform
        self._voweledform = voweledform
        self._type = type

    # Properties
    @property
    def unvoweledform(self):
        """Returns the unvoweled form of the suffix"""
        return self._unvoweledform

    @unvoweledform.setter
    def unvoweledform(self, value):
        """Sets the unvoweled form of the suffix"""
        self._unvoweledform = value

    @property
    def voweledform(self):
        """Returns the voweled form of the suffix"""
        return self._voweledform

    @voweledform.setter
    def voweledform(self, value):
        """Sets the voweled form of the suffix"""
        self._voweledform = value

    @property
    def type(self):
        """Returns the voweled form of the suffix"""
        return self._type

    @type.setter
    def type(self, value):
        """Sets the voweled form of the suffix"""
        self._type = value
