"""
VoweledNominalPatternsList.py
"""

"""
ALKHALIL MORPHO SYS -- An open source program.
Copyright (C) 2010.

This program is free software, distributed under the terms of
the GNU General Public License Version 3. For more information see the website at :
http://www.gnu.org/licenses/gpl.txt
"""

class VoweledNominalPatternsList:
    """
    This class provides implementations for the voweled nominal pattern lists.
    """

    def __init__(self):
        # Class Variables
        self._nominal_patterns = []

    # Public Methods

    def addPattern(self, vnp):
        """
        Adds a new voweled nominal pattern to the list.
        :param vnp: A voweled nominal pattern.
        """
        self._nominal_patterns.append(vnp)

    def getPatterns(self):
        """
        Returns the voweled nominal patterns list.
        :return: List of voweled nominal patterns.
        """
        return self._nominal_patterns
