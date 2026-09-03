"""
ToolWord.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class ToolWord:
    """
    This class provides implementations for Arabic tool words.
    Each tool word is characterized by its unvoweled form,
    voweled form, type, prefixes and suffixes classes and an attribute called priority to sort the results.
    """

    def __init__(self, unvoweledform, voweledform, type, prefixclass, suffixclass, priority):
        # Class Variables
        self._voweledform = voweledform
        self._unvoweledform = unvoweledform
        self._type = type
        self._prefixclass = prefixclass
        self._suffixclass = suffixclass
        self._priority = priority

    # Public Methods

    # Properties
    @property
    def unvoweledform(self):
        """Returns the unvoweled form of the tool word"""
        return self._unvoweledform
    @unvoweledform.setter
    def unvoweledform(self, value):
        """Sets the unvoweled form of the tool word"""
        self._unvoweledform = value

    @property
    def voweledform(self):
        """Returns the voweled form of the tool word"""
        return self._voweledform
    @voweledform.setter
    def voweledform(self, value):
        """Sets the voweled form of the tool word."""
        self._voweledform = value

    @property
    def type(self):
        """Returns the type of the tool word."""
        return self._type
    @type.setter
    def type(self, value):
        """Sets the type of the tool word."""
        self._type = value

    @property
    def prefixclass(self):
        """Returns the prefix compatibility classes of the tool word."""
        return self._prefixclass
    @prefixclass.setter
    def prefixclass(self, value):
        """Sets the prefix classes of the tool word."""
        self._prefixclass = value

    @property
    def suffixclass(self):
        """Returns the suffixe compatibility classes of the tool word."""
        return self._suffixclass
    @suffixclass.setter
    def suffixclass(self, value):
        """Sets the suffix classes of the tool word."""
        self._suffixclass = value

    @property
    def priority(self):
        """Returns the priority of the tool word."""
        return self._priority
    @priority.setter
    def priority(self, value):
        """Sets the priority classes of the tool word."""
        self._priority = value
