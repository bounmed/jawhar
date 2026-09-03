"""
Root.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class Root:
    """
    This class provides implementations for Arabic roots.
    Each root is characterized by its value and a set of voweled pattern ids separated by white space.
    """

    def __init__(self, val, vect):
        # Class Variables
        self._val = val
        self._vect = vect

    def __str__(self) -> str:
        return f"Root(val={self.val}, vect={self.vect})"

    # Public Methods
    @property
    def val(self):
        """Returns the value of the root."""
        return self._val

    @val.setter
    def val(self, value):
        """Sets the value of the root."""
        self._val = value

    @property
    def vect(self):
        """Returns the voweled patterns ids of the root."""
        return self._vect

    @vect.setter
    def vect(self, value):
        """Sets the voweled patterns ids of the root."""
        self._vect = value
