"""
VoweledVerbalPatternsList.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class VoweledVerbalPatternsList:
    """
    This class provides implementations for the voweled verbal pattern lists.
    """

    def __init__(self):
        # Class Variables
        self._verbal_patterns = []

    # Public Methods

    def addPattern(self, vvp):
        """
        Adds a new voweled verbal pattern to the list.
        :param vvp: A voweled verbal pattern.
        """
        self._verbal_patterns.append(vvp)

    def getPatterns(self):
        """
        Returns the voweled verbal patterns list.
        :return: List of voweled verbal patterns.
        """
        return self._verbal_patterns
