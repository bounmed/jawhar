"""
Suffix.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at:
http://www.gnu.org/licenses/gpl.txt
"""

class Suffix:
    """
    This class provides implementations for Arabic suffixes.
    Each suffix is characterized by its unvoweled form, voweled form, description, and its class for compatibility validation.
    """

    def __init__(self, unvoweledform, voweledform, desc, classe):
        # Class Variables
        self._unvoweledform = unvoweledform  # The unvoweled form of the suffix
        self._voweledform = voweledform    # The voweled form of the suffix
        self._desc = desc           # The description of the suffix
        self._classe = classe         # The class of the suffix

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
    def desc(self):
        """Returns the description of the suffix"""
        return self._desc

    @desc.setter
    def desc(self, value):
        """Sets the description of the suffix"""
        self._desc = value

    @property
    def classe(self):
        """Returns the class of the suffix"""
        return self._classe

    @classe.setter
    def classe(self, value):
        """Sets the class of the suffix"""
        self._classe = value
