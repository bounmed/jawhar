class Stem:
    """
    def __init__(self, unvoweledform, voweledforms, unvoweledform, unvoweledform):
        self.unvoweledform = unvoweledform
        self.voweledforms = voweledforms
        self.possiblepatterns = unvoweledform
        self.possibleroots = unvoweledform
    """
    def __init__(self, unvoweledform="", voweledforms=None, possiblepatterns=None, possibleroots=None):
        self._unvoweledform = unvoweledform
        self._voweledforms = voweledforms if voweledforms is not None else []
        self._possiblepatterns = possiblepatterns if possiblepatterns is not None else []
        self._possibleroots = possibleroots if possibleroots is not None else []
        self.lemma = ""

    def __str__(self) -> str:
        return f"Stem(unvoweledform={self.unvoweledform}, voweledforms={self.voweledforms}, entry={self.entry})"

    # Properties
    @property
    def lemma(self):
        """Returns the lemma  of the word"""
        return self._lemma
    @lemma.setter
    def lemma(self, value):
        """Sets the bw stem form of the stem"""
        self._lemma = value

    @property
    def unvoweledform(self):
        """Returns the unvoweled form of the stem"""
        return self._unvoweledform
    @unvoweledform.setter
    def unvoweledform(self, value):
        """Sets the unvoweled form of the stem"""
        self._unvoweledform = value

    @property
    def voweledforms(self):
        """Returns the voweled form of the stem"""
        return self._voweledforms
    @voweledforms.setter
    def voweledforms(self, value):
        """Sets the voweled form of the stem"""
        self._voweledforms = value

    @property
    def possiblepatterns(self):
        """Returns the possible patterns of the stem"""
        return self._possiblepatterns
    @possiblepatterns.setter
    def possiblepatterns(self, value):
        """Sets the possible patterns of the stem"""
        self._possiblepatterns = value

    @property
    def possibleroots(self):
        """Returns the possible roots of the stem"""
        return self._possibleroots
    @possibleroots.setter
    def possibleroots(self, value):
        """Sets the possible roots of the stem"""
        self._possibleroots = value

    def add_voweledform(self, voweledform):
        self.voweledforms.append(voweledform)

    def add_possiblepattern(self, possiblepattern):
        self.possiblepatterns.append(possiblepattern)

    def add_possibleroots(self, possibleroot):
        self.possibleroots.append(possibleroot)

    def get_stem_length(self):
        return len(self.unvoweledform)
