"""
UnvoweledPattern.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""


class UnvoweledPattern:
    """
    This class provides implementations for unvoweled Arabic patterns.
    Each pattern is characterized by its value, root extraction rules,
    and the IDs of all voweled forms of the pattern as defined in the XML databases.
    """

    def __init__(self, value, rules, ids):
        self._value = value  # The value of the pattern
        self._rules = rules  # Root extraction rules according to the pattern
        self._ids = ids    # IDs of all voweled forms of the pattern

    def __str__(self) -> str:
        return f"UnvoweledPattern(value={self.value}), ids={self.ids}, rules={self.rules}"

    # Properties
    @property
    def value(self):
        """Returns the value of the pattern"""
        return self._value

    @value.setter
    def value(self, value):
        """Sets the value of the pattern"""
        self._value = value

    @property
    def rules(self):
        """Returns the rules of the pattern"""
        return self._rules

    @rules.setter
    def rules(self, rules):
        """Sets the rules of the pattern"""
        self._rules = rules

    @property
    def ids(self):
        """Returns the IDs of the pattern"""
        return self._ids

    @ids.setter
    def ids(self, ids):
        """Sets the IDs of the pattern"""
        self._ids = ids
