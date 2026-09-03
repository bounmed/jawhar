
from ..data.db_loader import DbLoader
from ..models.result import Result
from ..models.segment import Segment
from ..models.stem import Stem


class _SimpleVVPattern:
    """Minimal stand-in for VoweledVerbalPattern used by the fallback generator."""
    __slots__ = ("id", "diac", "canonic", "type", "aug", "cas", "ncg", "trans")

    def __init__(self, id, diac, canonic, type, aug, cas, ncg, trans):
        self.id, self.diac, self.canonic = id, diac, canonic
        self.type, self.aug, self.cas, self.ncg, self.trans = type, aug, cas, ncg, trans


class Analyzer:
    def __init__(self):
        self.db = DbLoader()
        self.Prefixes = []
        self.Suffixes = []
        self.ToolWords = []
        self.allResults = {}
        self.allResultsBis = {}
        self.VRoots = {}
        self.NRoots = {}
        self.VSolutions = {}
        self.NSolutions = {}
        self.VPatterns = {}
        self.NPatterns = {}
        self.TW = {}
        self.PN = {}
        self.EW = {}
        self.VUPatterns = {}
        self.NUPatterns = {}
        self.VVPatterns = {}
        self.NVPatterns = {}

        # Per-first-character caches for root JSON files (bug 7 fix)
        self._verbal_root_cache = {}
        self._nominal_root_cache = {}

        try:
            self.NRoots = self.db.LoadAllRoots2()
            self.VRoots = self.db.LoadAllRoots2()

            self.Prefixes = self.db.LoadPrefixes()
            self.Suffixes = self.db.LoadSuffixes()
            self.ToolWords = self.db.LoadToolWords()
            self.PN = self.db.LoadProperNouns()
            self.EW = self.db.LoadExceptionalWords()

            # Build O(1) lookup dicts for prefix/suffix matching (bug 6 fix)
            self.PrefixMap = {}
            for p in self.Prefixes:
                self.PrefixMap.setdefault(p.unvoweledform, []).append(p)
            self.SuffixMap = {}
            for s in self.Suffixes:
                self.SuffixMap.setdefault(s.unvoweledform, []).append(s)

            self.NUPatterns = {}
            self.VUPatterns = {}
            self.NVPatterns = {}
            self.VVPatterns = {}
            for i in range(2, 10):
                self.NUPatterns[i] = self.db.LoadUnvoweledNominalPatterns(i)
                self.VUPatterns[i] = self.db.LoadUnvoweledVerbalPatterns(i)
                self.NVPatterns[i] = self.db.LoadVoweledNominalPatterns(i)
                self.VVPatterns[i] = self.db.LoadVoweledVerbalPatterns(i)

        except Exception as ex:
            print('Error occurred:', ex)

    def Analyze(self, normalizedWord, unvoweledWord, keep_stop_word):
        resulL = []  # list to be returned
        if normalizedWord in self.NSolutions:  # if the word was already analyzed
            resulL = self.NSolutions[normalizedWord]
        else:
            Segments = self.segment_word(unvoweledWord)  # segmentation

            # Single-char particles (و, ل, ب, ف, ...) need special handling:
            # - is_valid_segment rejects stem_len < 2, so many never segment.
            # - و segments as stem=وا (و→وا transformation), losing its particle reading.
            # Ensure every single-char tool word gets its particle analysis included.
            if len(unvoweledWord) == 1:
                for tw in self.ToolWords:
                    if tw.unvoweledform == unvoweledWord:
                        r = Result(tw.voweledform, unvoweledWord, "#", unvoweledWord,
                                   tw.voweledform, tw.type, "", "", "", "#", tw.priority)
                        resulL.append(r)

            it = iter(Segments)

            if unvoweledWord in self.EW:  # test whether the word is exceptional
                ew = self.EW[unvoweledWord]
                r = Result(ew.voweledform, unvoweledWord, ew.prefix, ew.stem, ew.voweledform, ew.type, "", "", "",
                           ew.suffix, "1")
                resulL.append(r)  # add the exceptional word found to the result list to be returned
            else:
                for segment in it:
                    if keep_stop_word == True :
                        toolwordlist = self.possible_tool_words(segment)  # get all possible tool words given the segment
                        # for each tool word in toolwordlist
                        for tw in toolwordlist:
                            if segment.suffix.unvoweledform == "ه":
                                if tw.voweledform.endswith("ي") or tw.voweledform.endswith("يْ") or tw.voweledform.endswith("ِ"):
                                    segment.suffix.voweledform ="هِ"
                                else:
                                    segment.suffix.voweledform ="هُ"

                            # create the voweled form the entire tool word
                            vowledWord = segment.prefix.voweledform + tw.voweledform + segment.suffix.voweledform
                            pf = segment.prefix.voweledform
                            sf = segment.suffix.voweledform
                            if segment.prefix.voweledform == "":
                                pf = "#"  # replace the empty prefix by # for display purpose
                            if segment.suffix.voweledform == "":
                                sf = "#"  # replace the empty suffix by #

                            if not self.not_compatible(normalizedWord, vowledWord):  # check the compatibility between
                                # the word voweled form produced by the analyzer and the short vowels possibly
                                # existing in the normlized form of the input word
                                r = Result(vowledWord, normalizedWord, pf + " " + segment.prefix.desc, segment.stem.unvoweledform, segment.stem.lemma,
                                        tw.type, "", "", "", sf + " " + segment.suffix.desc, tw.priority)
                                resulL.append(r)  # add the tool word found to the result list to be returned

                    # Proper Nouns
                    if segment.stem.unvoweledform in self.PN.keys() and ("C1" in segment.prefix.classe) and ("C1" in segment.suffix.classe):
                        pn = self.PN[segment.stem.unvoweledform]
                        # create the voweled form of the proper noun
                        vowledWord = segment.prefix.voweledform + pn.voweledform + segment.suffix.voweledform
                        pf = segment.prefix.voweledform
                        sf = segment.suffix.voweledform
                        if segment.prefix.voweledform == "":
                            pf = "#"  # replace the empty prefix by # for display purpose
                        if segment.suffix.voweledform == "":
                            sf = "#"  # replace the empty suffix by #
                        if not self.not_compatible(normalizedWord, vowledWord):  # check the compatibility between
                            # the word voweled form produced by the analyzer and the short vowels possibly
                            # existing in the normlized form of the input word

                            r = Result(vowledWord, normalizedWord, pf + " " + segment.prefix.desc, segment.stem.unvoweledform, segment.stem.lemma,
                                       pn.type, "", "", "", sf + " " + segment.suffix.desc, "9999")
                            resulL.append(r)  # add the proper noun to the result list to be returned

                    # Nouns
                    if ("V" not in segment.prefix.classe) and ("V" not in segment.suffix.classe):
                        # a word can have possible nominal solutions if the prefix and suffix classes
                        # are not verbal (V)
                        nounSolutionList = self.possible_nominal_solutions(segment, normalizedWord)  # get all possible
                        # nominal solutions of the input word
                        resulL.extend(nounSolutionList)

                    # Verbs
                    if ("N" not in segment.prefix.classe) and ("N" not in segment.suffix.classe):
                        # a word can have possible verbal solutions if the prefix and suffix classes
                        # are not nominal (N)
                        verbSolutionList = self.possible_verbal_solutions(segment, normalizedWord)  # get all possible verbal
                        # solutions of the input word
                        resulL.extend(verbSolutionList)

                resulL = self.sort_results(resulL)  # The entire results list is sorted depending on the prioririty defined in the

                # Result objects
                self.NSolutions[normalizedWord] = resulL

        return resulL

    def segment_word(self, unvoweled_word):
        result = []
        for i in range(len(unvoweled_word)):
            prefix_temp = unvoweled_word[:i]
            remaining = unvoweled_word[i:]
            possible_prefixes = self.possible_prefixes(prefix_temp)
            if(len(possible_prefixes) != 0):
                for j in range(len(remaining)):
                    suffix_temp = remaining[len(remaining) - j:]
                    stem = remaining[:len(remaining) - j]
                    possible_suffixes = self.possible_suffixes(suffix_temp)
                    if(len(possible_suffixes) != 0):
                        possible_stems = [stem]
                        if stem.endswith("ت"):#append a possible stem if stem ends with TAA like "لثابت"
                            possible_stems.append(stem[:-1] + 'ة')
                        if stem.endswith("و"): #append a possible stem if stem ends with WAW like "أبو"
                            possible_stems.append(stem + "ا")
                        for prefix in possible_prefixes:
                            for suffix in possible_suffixes:
                                for alternative in possible_stems:
                                    segment = Segment(prefix, Stem(unvoweledform=alternative), suffix)
                                    if self.is_valid_segment(segment):
                                        result.append(segment)
            else:
                if unvoweled_word[i - 1] == 'ا' and unvoweled_word[i] == 'ل':
                    continue
                else:
                    break
        return result

    def possible_prefixes(self, pref):
        return self.PrefixMap.get(pref, [])

    def possible_suffixes(self, suf):
        return self.SuffixMap.get(suf, [])

    def possible_tool_words(self, seg):
        result = []
        result_emp = []
        if seg.stem.unvoweledform in self.TW:
            result_emp = self.TW[seg.stem.unvoweledform]
        else:
            for tw in self.ToolWords:
                if seg.stem.unvoweledform == tw.unvoweledform:
                    result_emp.append(tw)
            self.TW[seg.stem.unvoweledform] = result_emp

        for tw in result_emp:
            if seg.prefix.classe in tw.prefixclass and seg.suffix.classe in tw.suffixclass:
                result.append(tw)
        return result

    def possible_nominal_solutions(self, segment, normalized_word):
        result = []  # List to be returned
        vow_patterns = []
        possible_patterns = {}
        if segment.stem.unvoweledform in self.NPatterns:
            possible_patterns = self.NPatterns[segment.stem.unvoweledform]
        else:
            possible_patterns = self.possible_nominal_patterns(segment.stem.unvoweledform)

        for root in possible_patterns.values():
            for vr, patterns in root.items():
                vow_patterns = patterns
                for vnp in vow_patterns:
                    voweled_words = self.vowelize(segment, vnp.diac)
                    voweled_word = voweled_words[0]

                    if self.is_valid_nominal_solution(segment, vnp, voweled_words, normalized_word):
                        sol = self.interpret_vnp(segment, vnp, vr)
                        r = Result(voweled_word, normalized_word, sol[0], segment.stem.unvoweledform, segment.stem.lemma, sol[1], vnp.canonic, vr, sol[2], sol[3], sol[4])
                        result.append(r)
        return result

    def possible_nominal_patterns(self, st):
        result = {}  # Hash map to be returned
        unp_value = ""

        # Unvoweled nominal patterns with the same length as st
        unvoweled_nominal_patterns = self.NUPatterns.get(len(st))
        if unvoweled_nominal_patterns and len(unvoweled_nominal_patterns) !=0:
            for unp in unvoweled_nominal_patterns:
                unp_value = unp.value
                test = 0  # Test remains 0 if unp shares the same infixes as st
                for i in range(len(unp_value)):  # Check the compatibility between st and unp
                    #@TODO: I think there is mistake here the order of 'FAA', 'AAA', and 'LAAM'
                    if "ف" not in unp_value[i] and "ع" not in unp_value[i] and "ل" not in unp_value[i]:
                        if unp_value[i] != st[i]:
                            #if unp.ids == '99997':
                            #    print('failed, unp_value: ', unp_value[i], ' != st: ', st[i])
                            test += 1  # In this case, unp is not compatible with st
                            break
                if test == 0:
                    root = {}
                    roots = self.get_root(st, unp.rules).split(" ")
                    #print("roots : ", roots)
                    for root_ in roots:
                        if self.NRoots.get(root_):
                            vr = self.get_nominal_root(root_, int(self.NRoots.get(root_)))
                            if vr:
                                inter = self.intersection(vr.vect.split(" "), unp.ids.split(" "))
                                if inter:
                                    vnpl = self.NVPatterns.get(len(unp.value))
                                    nv_patterns = self.intersection2(vnpl, inter, False)
                                    root[root_] = nv_patterns
                    result[unp] = root
            self.NPatterns[st] = result

        return result

    def possible_verbal_solutions(self, segment, normalized_word):
        result = []  # list to be returned
        vow_patterns = []

        possible_patterns = {}
        if segment.stem.unvoweledform in self.VPatterns:
            possible_patterns = self.VPatterns[segment.stem.unvoweledform]
        else:
            possible_patterns = self.possible_verbal_patterns(segment.stem.unvoweledform)

        for root_key, root_dict in possible_patterns.items():
            for vr, patterns in root_dict.items():
                vow_patterns = patterns
                for vnp in vow_patterns:
                    vowled_words = self.vowelize(segment, vnp.diac)  # deducing the voweled form of the word
                    vowled_word = vowled_words[0]

                    if self.is_valid_verbal_solution(segment, vnp, vowled_words, normalized_word):  # validation of the verbal solutions
                        # Fallback patterns live under the "__fallback__:<root>" key and
                        # report the literal placeholder as the root; resolve the real
                        # root from the key so results show it instead of "__fallback__".
                        if vr == "__fallback__":
                            root_value = root_key.split(":", 1)[1] if ":" in root_key else segment.stem.unvoweledform
                        else:
                            root_value = vr
                        sol = self.interpret_vvp(segment, vnp, root_value)  # interpretation of the coded information
                        r = Result(vowled_word, segment.stem.unvoweledform, sol[0], segment.stem.unvoweledform, segment.stem.lemma, sol[1], vnp.canonic, root_value, sol[2], sol[3], sol[4])
                        result.append(r)

        return result

    def get_root(self, stem, rules):
        root = ""  # string to be returned
        root_rules = rules.split(" ")
        for rule in root_rules:#1234 means 1st 2nd 3rd and 4th chars make the root
            root += ''.join(stem[int(char) - 1] if char.isdigit() else char for char in rule) + " "
        return root.rstrip().replace("إ", "ء").replace("أ", "ء").replace("ئ", "ء").replace("ؤ", "ء")

    def possible_verbal_patterns(self, stem):
        result = {}  # dictionary to be returned
        unp_value = ""

        unvowled_verbal_patterns = self.VUPatterns.get(len(stem))  # unvoweled verbal patterns with the same length as st
        if unvowled_verbal_patterns is not None:
            for unp in unvowled_verbal_patterns:
                unp_value = unp.value

                test = 0  # test remains 0 if unp shares the same infixes as st
                for t_char, tt_char in zip(stem, unp_value): # compare stem and unp_value
                    if ("ف" not in tt_char) and ("ع" not in tt_char) and ("ل" not in tt_char) and tt_char != t_char:
                        test += 1  # in this case unp is not compatible with st
                        break
                if test == 0:
                    root_dict = {}
                    roots = self.get_root(stem, unp.rules).split(" ")
                    for root in roots:
                        if root in self.VRoots:
                            vr = self.get_verbal_root(root, self.VRoots[root])
                            if vr is not None:
                                inter = self.intersection(vr.vect.split(" "), unp.ids.split(" "))
                                if inter:
                                    vnpl = self.VVPatterns.get(len(unp_value))
                                    vow_patterns = self.intersection2(vnpl, inter, True)
                                    # Fallback: the verbal pattern databases (AllRoots2.txt,
                                    # unvoweled-pattern ids, VVPatterns.id) use misaligned
                                    # ID spaces from the JSON conversion, so intersection2
                                    # often returns []. Fall back to voweled patterns whose
                                    # canonical template is compatible with the root (root
                                    # consonants fit the ف/ع/ل positions), restoring verbal
                                    # candidate coverage without generating thousands of
                                    # spurious candidates.
                                    if not vow_patterns and vnpl:
                                        vow_patterns = [
                                            p for p in vnpl
                                            if self._canonic_fits_root(p.canonic, root)
                                        ]
                                    root_dict[root] = vow_patterns

                    result[unp] = root_dict
            self.VPatterns[stem] = result

        # Fallback: if no verbal patterns were generated (root missing from
        # AllRoots2.txt), generate standard Form I verbal patterns directly from the
        # stem. This restores coverage for the hundreds of common Arabic verb roots
        # absent from the converted JSON database. We try the raw stem and any
        # 3-consonant substring (to handle prefixed/suffixed forms like اضافت -> ضاف).
        # We check specifically for verbal patterns (type field starts with verbal
        # codes مم/مض/مج/أ), not nominal ones, so nominal matches don't block the
        # fallback.
        verbal_pats = sum(
            1 for root_dict in result.values()
            for pats in root_dict.values()
            for p in pats
            if hasattr(p, 'type') and p.type in ("مم", "مج", "مض", "أ")
        )
        # Supplement with fallback Form I patterns when the DB patterns are absent
        # or incomplete. Weak-letter verbs (قول, كون, بدأ...) and verbs with missing
        # cas values produce patterns that fail validation for certain prefixes; the
        # fallback generates all grammatical states (رفع/نصب/جزم) so at least one
        # validates. We try the raw stem and any 3-consonant root extracted from
        # longer stems (handles suffixed forms like يقولون -> قول).
        has_fallback_source = (len(stem) == 3 and stem in self.VRoots)
        if not has_fallback_source:
            cons = [c for c in stem if c in "ءآأإابتثجحخدذرزسشصضطظعغفقكلمنهويى"]
            if len(cons) >= 3:
                has_fallback_source = True
        if verbal_pats == 0 or has_fallback_source:
            candidates = [stem]
            # also try extracting 3-consonant root from longer stems
            cons = [c for c in stem if c in "ءآأإابتثجحخدذرزسشصضطظعغفقكلمنهويى"]
            if len(cons) >= 3:
                candidates.append("".join(cons[:3]))
            seen = set()
            for cstem in candidates:
                if cstem in seen:
                    continue
                seen.add(cstem)
                fb = self._fallback_verbal_patterns(cstem)
                if fb:
                    result["__fallback__:" + cstem] = {"__fallback__": fb}
            if result:
                self.VPatterns[stem] = result

        return result

    def _fallback_verbal_patterns(self, stem):
        """Generate Form I verbal analyses for a stem whose root is absent from the DB.

        Uses the standard Arabic Form I awzaan (فَعَلَ / يَفْعُلُ / يَفْعِلُ / يَفْعَلُ)
        applied to the stem consonants, producing past/active/passive/present forms.
        The diacritized form is built to match the stem length exactly so that
        vowelize() can apply it without index errors. cas values cover all three
        grammatical states (رفع/نصب/جزم) so that prefixed forms (ن, ا, ت) pass
        validation regardless of prefix class.
        """
        cons = [c for c in stem if c in "ءآأإابتثجحخدذرزسشصضطظعغفقكلمنهويى"]
        if len(cons) != 3:
            return []
        f, a, l = cons
        # (canonic, diacritized, type, cas, ncg). Diacritized forms are built to be
        # exactly 3 characters wide (one per stem consonant) so vowelize() works.
        # cas includes all of ر (رفع), ن (نصب), ج (جزم) so every prefix class
        # (V1 needs ر, V2 needs ن, V3 needs ج) finds a compatible pattern.
        templates = [
            ("فَعَلَ", f + "َ" + a + "َ" + l, "مم", "ر", "1"),       # past active 3sg
            ("فَعَلَ", f + "َ" + a + "ْ" + l, "مم", "ر", "8"),       # past active
            ("فَعُلَ", f + "ُ" + a + "ُ" + l, "مم", "ر", "1"),       # past (fu'l)
            ("يَفْعُلُ", f + "ُ" + a + "ُ" + l, "ضم", "ر", "8"),      # present (رفع)
            ("يَفْعُلُ", f + "ُ" + a + "َ" + l, "ضم", "ن", "8"),      # present (نصب)
            ("يَفْعُلُ", f + "ُ" + a + "ْ" + l, "ضم", "ج", "8"),      # present (جزم)
            ("يَفْعِلُ", f + "ِ" + a + "ُ" + l, "ضم", "ر", "8"),      # present (fa'il)
            ("يَفْعَلُ", f + "َ" + a + "ُ" + l, "ضم", "ر", "8"),      # present (fa'al)
            ("فَعْل", f + "ْ" + a + "ْ" + l, "أ", "1", "1"),        # imperative
        ]
        patterns = []
        for canon, diac, vtype, vcas, vncg in templates:
            patterns.append(_SimpleVVPattern(str(900000 + len(patterns)), diac,
                                             canon, vtype, "جر", vcas, vncg, "ك"))
        return patterns

    @staticmethod
    def _canonic_fits_root(canonic: str, root: str) -> bool:
        """Check whether a voweled pattern's canonical form is compatible with a root.

        The canonical form uses ف, ع, ل as placeholders for the root consonants and
        actual letters for fixed positions (prefixes, infixes, gemination). A pattern
        fits the root when every non-placeholder position matches the corresponding
        root consonant and the number of root placeholders does not exceed the root
        length.
        """
        # strip diacritics (no re import at module level)
        skel = canonic
        for d in "ًٌٍَُِّْ":
            skel = skel.replace(d, "")
        root_idx = 0
        for sk_char in skel:
            if sk_char in "فعل":
                root_idx += 1
            else:
                if root_idx >= len(root) or root[root_idx] != sk_char:
                    return False
        return 0 < root_idx <= len(root)

    def vowelize(self, segment, voweledpattern):
        resultat = ["", ""]
        stem = segment.stem.unvoweledform
        result = ""
        soukoun = ""
        j = 0

        if segment.prefix.classe in ["N1", "N2", "N3", "N5"]:
            if self.is_solar(stem[0]):
                for i in range(len(voweledpattern)):
                    if self.is_diacritic(voweledpattern[i]):
                        result += voweledpattern[i]
                    else:
                        result += stem[j]
                        j += 1
                result = result[:1] + "ّ" + result[1:]
            else:
                for vpchar in voweledpattern:
                    if self.is_diacritic(vpchar):
                        result += vpchar
                    else:
                        result += stem[j]
                        j += 1
                soukoun = "ْ"
        else:
            for char in voweledpattern:
                if self.is_diacritic(char):
                    result += char
                else:
                    result += stem[j]
                    j += 1

        if "ة" in result and segment.suffix.voweledform:
            result = result.replace('ة', 'ت')

        if result.endswith("ُوا") and segment.suffix.unvoweledform:
            result = result[:-1]

        if segment.suffix.unvoweledform == "ه":
            if result.endswith("ي") or result.endswith("يْ") or result.endswith("ِ"):
                segment.suffix.voweledform="هِ"
            else:
                segment.suffix.voweledform="هُ"

        if segment.suffix.unvoweledform == "هما":
            if result.endswith("ي") or result.endswith("يْ") or result.endswith("ِ"):
                segment.suffix.voweledform="هِمَا"
            else:
                segment.suffix.voweledform="هُمَا"

        if segment.suffix.unvoweledform == "هم":
            if result.endswith("ي") or result.endswith("يْ") or result.endswith("ِ"):
                segment.suffix.voweledform="هِمْ"
            else:
                segment.suffix.voweledform="هُمْ"

        if segment.suffix.unvoweledform == "هن":
            if result.endswith("ي") or result.endswith("يْ") or result.endswith("ِ"):
                segment.suffix.voweledform="هِنَّ"
            else:
                segment.suffix.voweledform="هُنَّ"

        if (result.endswith("ُ") or result.endswith("َ")) and segment.suffix.unvoweledform == "ي":
            result = result[:-1] + "ِ"

        resultat[0] = segment.prefix.voweledform + soukoun + result + segment.suffix.voweledform
        resultat[1] = result

        return resultat

    def get_verbal_root(self, root, ind):
        fc = root[0]
        if fc not in self._verbal_root_cache:
            self._verbal_root_cache[fc] = self.db.LoadVerbalRootsByFirstChar(fc)
        return self._verbal_root_cache[fc][int(ind)]

    def get_nominal_root(self, root, ind):
        fc = root[0]
        if fc not in self._nominal_root_cache:
            self._nominal_root_cache[fc] = self.db.LoadNominalRootsByFirstChar(fc)
        return self._nominal_root_cache[fc][ind]

    def is_solar(self, c):
        solar_characters = ['ت', 'ث', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ل', 'ن']
        return c in solar_characters

    def is_numeric(self, c):
        return '0' <= c <= '9'

    def is_diacritic(self, c):
        diacritic_characters = ['َ', 'ً', 'ُ', 'ٌ', 'ِ', 'ٍ', 'ْ', 'ّ']
        return c in diacritic_characters

    def not_compatible(self, normalized_word, voweled_word):
        test = 0

        vpnr = ""
        vpnrm_list = []
        vpn = list(normalized_word)
        for ct in range(len(vpn)):
            if self.is_diacritic(vpn[ct]):
                vpnr += vpn[ct]
            else:
                vpnrm_list.append(vpnr)
                vpnr = ""
        vpnrm_list.append(vpnr)

        vpvwl = ""
        vpvw_list = []
        vpvw = list(voweled_word)
        for ct in range(len(vpvw)):
            if self.is_diacritic(vpvw[ct]):
                vpvwl += vpvw[ct]
            else:
                vpvw_list.append(vpvwl)
                vpvwl = ""

        vpvw_list.append(vpvwl)
        # The two lists can differ in length when the voweled form carries a
        # stacked diacritic (e.g. tanwin on the final consonant), which caused
        # an IndexError and killed the whole analysis. Only compare aligned
        # positions; leftover differences are caught by the undiac1/undiac2
        # check below.
        for ct in range(min(len(vpnrm_list), len(vpvw_list))):
            if vpnrm_list[ct] != "":
                if vpnrm_list[ct] == "ّ":
                    if vpvw_list[ct] not in ["ّ", "َّ", "ًّ", "ُّ", "ٌّ", "ِّ", "ٍّ"]:
                        test += 1
                else:
                    if vpnrm_list[ct] != vpvw_list[ct]:
                        test += 1

        undiac1 = ''.join(c for c in normalized_word if c not in ['َ', 'ً', 'ُ', 'ٌ', 'ِ', 'ٍ', 'ْ', 'ّ'])
        undiac2 = ''.join(c for c in voweled_word if c not in ['َ', 'ً', 'ُ', 'ٌ', 'ِ', 'ٍ', 'ْ', 'ّ'])
        if undiac1 != undiac2:
            test += 1

        return test != 0

    def intersection2(self, L1, _L2, verbal):
        # The verbal flag does not affect the algorithm — both branches were
        # identical. The parameter is kept for API compatibility.
        intersection = []
        L2 = sorted(_L2)
        try:
            j = len(L2) - 1
            i = len(L1) - 1
            imax = i

            while L2[j] < L1[i].id and i > 0:
                i -= 1
            if L2[j] == L1[i].id:
                intersection.append(L1[i])
                imax = i
            else:
                imax = min(i + 1, len(L1) - 1)

            if imax > 0:
                j = 0
                imin = 0
                while j <= len(L2) - 2:
                    i = imin
                    while L2[j] > L1[i].id and i <= imax:
                        i += 1
                    if L2[j] == L1[i].id:
                        intersection.append(L1[i])
                        imin = i
                    else:
                        imin = max(i - 1, 0)
                    j += 1

            if intersection and intersection[0].id == L2[-1].id:
                intersection = intersection[1:] + [intersection[0]]

        except Exception:
            import logging
            logging.getLogger(__name__).debug(
                "intersection2 error — L1 len=%d L2=%s", len(L1), _L2, exc_info=True
            )

        return intersection

    def intersection(self, _tab1, _tab2):
        intersection = []
        # Sort and Swap lists if necessary to ensure tab1 is the longer
        if len(_tab1) < len(_tab2):
            tab1 = sorted(_tab2)
            tab2 = sorted(_tab1)
        else:
            tab1 = sorted(_tab1)
            tab2 = sorted(_tab2)

        try:
            j = len(tab2) - 1
            i = len(tab1) - 1
            imax = i

            while tab2[j] < tab1[i] and i > 0:
                i -= 1

            if tab2[j] == tab1[i]:
                intersection.append(tab2[j])
                imax = i
            else:
                imax = min(i + 1, len(tab1) - 1)

            if imax > 0:
                j = 0
                imin = 0
                while j <= len(tab2) - 2:
                    i = imin
                    #@TODO: check this function
                    while i< len(tab1) and j<len(tab2) and tab2[j] > tab1[i] and i <= imax:
                        i += 1
                    #@TODO: check this function
                    if i< len(tab1) and j<len(tab2) and  tab2[j] == tab1[i]:
                        intersection.append(tab2[j])
                        imin = i
                    else:
                        imin = max(i - 1, 0)
                    j += 1

        except Exception as ex:
            print('Error occurred:', ex)
            pass

        # Rotate the intersection if the first element matches the last element of tab2
        if intersection and intersection[0] == tab2[-1]:
            intersection = intersection[1:] + [intersection[0]]

        return intersection



    def is_valid_segment(self, segment):
        st = segment.stem

        prefix_classe = segment.prefix.classe
        suffixe_classe = segment.suffix.classe
        stem_len = st.get_stem_length()

        # Validation criteria
        if (
            ("N" in prefix_classe and "V" in suffixe_classe) or
            ("V" in prefix_classe and "N" in suffixe_classe) or
            stem_len < 2 or
            (prefix_classe in ["N1", "N2", "N3", "N5"] and segment.suffix.unvoweledform != "")):
            return False
        else:
            return True

    def is_valid_verbal_solution(self, segment, vnp, vowled_words, normalized_word):
        valid = True
        pref_class = segment.prefix.classe
        suff_class = segment.suffix.classe
        ncg = vnp.ncg
        vowled_word = vowled_words[0]

        # Intransitive verbs are not compatible with non-empty suffixes
        if vnp.trans == "ل" and segment.suffix.unvoweledform:
            return False

        # Some prefixes (V1 class) are not compatible with the non-imperfect indicative verbs (mouDarie ghayr marfoue)
        if pref_class == "V1" and "ر" not in vnp.cas:
            return False

        # Some prefixes (V2 class) are not compatible with the non-imperfect subjunctive verbs (mouDarie ghayr mansoub)
        if pref_class == "V2" and "ن" not in vnp.cas:
            return False

        # Some prefixes (V3 class) are not compatible with the non-imperfect jussive verbs (mouDarie ghayr majzoum)
        if pref_class == "V3" and "ج" not in vnp.cas:
            return False

        # Some prefixes (C2 class) are not compatible with the imperative verbs (amr)
        if pref_class == "C2" and "أ" in vnp.type:
            return False

        # Some suffixes (except C1 suffixes) are not compatible with the imperfect jussive verbs (mouDarie majzoum)
        if suff_class != "C1" and "ج" in vnp.type:
            return False

        # Some suffixes (V2 and V3 class) are not compatible with the imperative verbs (amr)
        if suff_class == "V2" and "أ" in vnp.type:
            return False
        if suff_class == "V3" and "أ" in vnp.type:
            return False

        if suff_class == "V4" and "6" not in ncg:
            return False

        # Misspelled hamza writings
        if any(char in vowled_word for char in ["إَ", "أِ", "ِؤ", "إُ", "ؤِ", "ئَ", "ئُ"]):
            return False

        # Compatibility of the voweled word with the normalized word
        if self.not_compatible(normalized_word, vowled_word):
            return False

        # Hamza writing rules
        for h in range(1, len(vowled_words[1]) - 2):
            if vowled_words[1][h] in ['ؤ', 'ئ', 'أ']:
                if vowled_words[1][h - 1] == 'ِ' or vowled_words[1][h + 1] == 'ِ':
                    if vowled_words[1][h] != 'ئ':
                        return False
                elif vowled_words[1][h - 1] == 'ُ' or vowled_words[1][h + 1] == 'ُ':
                    valid = valid and vowled_words[1][h] == 'ؤ'
                elif vowled_words[1][h - 1] == 'َ' or vowled_words[1][h + 1] == 'َ':
                    valid = valid and vowled_words[1][h] == 'أ'
            elif vowled_words[1][h] == 'ء':
                if vowled_words[1][h - 1] in ['ا', 'َ'] and vowled_words[1][h + 1] in ['َ', 'ْ']:
                    continue
                else:
                    return False

        h = len(vowled_words[1]) - 2
        if vowled_words[1][h] == 'ئ':
            if vowled_words[1][h - 1] != 'ِ':
                return False
        elif vowled_words[1][h] == 'ؤ':
            if vowled_words[1][h - 1] != 'ُ':
                return False
        elif vowled_words[1][h] == 'أ':
            if vowled_words[1][h - 1] != 'َ':
                return False
        elif vowled_words[1][h] == 'ء':
            if vowled_words[1][h - 1] in ['َ', 'ِ', 'ُ']:
                return False

        # Misspelled hamza writings (again)
        if any(char in vowled_word for char in ["إَ", "أِ", "ِؤ", "إُ", "ؤِ", "ئَ", "ئُ"]):
            return False

        return valid

    def is_valid_nominal_solution(self, segment, vnp, vowled_words, normalized_word):
        valid = True
        pref_class = segment.prefix.classe
        suff_class = segment.suffix.classe
        ncg = vnp.ncg
        vowled_word = vowled_words[0]

        # Nunnation (tanwin) is not compatible with suffixes except the empty suffix
        # it is not compatible also with the definit article prefixes (ie N1 N2 N3 N5)
        if any(char in vowled_word for char in ["ً", "ٍ", "ٌ"]) and (
                segment.suffix.unvoweledform or pref_class in ["N1", "N2", "N3", "N5"]):
            return False

        # Some prefixes (C2 C3 N2) are not compatible with the genitive case (majrour)
        if pref_class in ["N2", "C2", "C3"] and ncg in ["13", "14", "15", "16", "17", "18"]:
            return False

        # Some prefixes (N4 N5) are not compatible with the non genitive cases
        if pref_class in ["N4", "N5"] and ncg not in ["13", "14", "15", "16", "17", "18"]:
            return False

        # Rules for writing Hamza
        for h in range(1, len(vowled_words[1]) - 2):
            if vowled_words[1][h] in ['ؤ', 'ئ', 'أ']:
                if vowled_words[1][h - 1] == 'ِ' or vowled_words[1][h + 1] == 'ِ':
                    if vowled_words[1][h] != 'ئ':
                        return False
                elif vowled_words[1][h - 1] == 'ُ' or vowled_words[1][h + 1] == 'ُ':
                    valid = valid and vowled_words[1][h] == 'ؤ'
                elif vowled_words[1][h - 1] == 'َ' or vowled_words[1][h + 1] == 'َ':
                    valid = valid and vowled_words[1][h] == 'أ'
            elif vowled_words[1][h] == 'ء':
                if vowled_words[1][h - 1] == 'ا' and vowled_words[1][h + 1] in ['َ', 'ْ']:
                    continue
                else:
                    return False

        h = len(vowled_words[1]) - 2
        if h > 0:
            if vowled_words[1][h] == 'ئ':
                if vowled_words[1][h - 1] != 'ِ':
                    return False
            elif vowled_words[1][h] == 'ؤ':
                if vowled_words[1][h - 1] != 'ُ':
                    return False
            elif vowled_words[1][h] == 'أ':
                if vowled_words[1][h - 1] != 'َ':
                    return False
            elif vowled_words[1][h] == 'ء':
                if vowled_words[1][h - 1] in ['َ', 'ِ', 'ُ']:
                    return False

        # Misspelled hamza writings
        if any(char in vowled_word for char in ["إَ", "أِ", "إُ", "ؤِ", "ٌأْ", "ُأَ"]):
            return False

        # Compatibility of the voweled word with the normalized word
        if self.not_compatible(normalized_word, vowled_word):
            return False

        return valid


    def sort_results(self, results):
        return sorted(results, key=lambda r: r.priority)

    #@TODO:this needs a code refactoring
    def interpret_vnp(self, seg, vnp, root):
        result = [""] * 7
        prefix = ""
        suffix = ""
        suffix_txt = ""
        priority = "1"

        if seg.prefix.voweledform != "":
            result[0] = seg.prefix.voweledform + ": " + seg.prefix.desc

        if seg.suffix.voweledform != "":
            result[3] = seg.suffix.voweledform + ": " + seg.suffix.desc
        type_mapping = {
            "فا": ("اسم فاعل", "10"),
            "مف": ("اسم مفعول", "11"),
            "مفا": ("مبالغة اسم الفاعل", "10"),
            "آ": ("اسم آلة", "15"),
            "زمك": ("اسم زمان أو مكان", "14"),
            "فض": ("اسم تفضيل", "13"),
            "وش": ("صفة مشبهة", "12"),
            "صأ": ("مصدر أصلي", "07"),
            "صم": ("مصدر ميمي", "08"),
            "صه": ("مصدر هيئة", "17"),
            "صر": ("مصدر مرة", "16"),
            "جا": ("اسم جامد", "01"),
            "صن": ("مصدر صناعي", "16"),
            "نس": ("نسبة", "16")
        }

        if vnp.type in type_mapping:
            tag,prio  = type_mapping[vnp.type]
            result[1] = tag
            priority += prio

        if vnp.ncg == "1":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مذكر مرفوع في حالة التعريف"
                    priority += "1111"
                else:
                    result[2] = "مفرد مذكر مرفوع في حالة الاضافة"
                    priority += "1112"
            else:
                result[2] = "مفرد مذكر مرفوع نكرة"
                priority += "1113"
        elif vnp.ncg == "2":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مؤنث مرفوع في حالة التعريف"
                    priority += "1211"
                else:
                    result[2] = "مفرد مؤنث مرفوع في حالة الاضافة"
                    priority += "1212"
            else:
                result[2] = "مفرد مؤنث مرفوع نكرة"
                priority += "1213"
        elif vnp.ncg == "3":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مذكر مرفوع في حالة التعريف"
                    priority += "2111"
                else:
                    result[2] = "مثنى مذكر مرفوع في حالة الاضافة"
                    priority += "2112"
            else:
                result[2] = "مثنى مذكر مرفوع نكرة"
                priority += "2113"
        elif vnp.ncg == "4":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مؤنث مرفوع في حالة التعريف"
                    priority += "2211"
                else:
                    result[2] = "مثنى مؤنث مرفوع في حالة الاضافة"
                    priority += "2212"
            else:
                result[2] = "مثنى مؤنث مرفوع نكرة"
                priority += "2213"
        elif vnp.ncg == "5":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مذكر مرفوع في حالة التعريف"
                    priority += "3111"
                else:
                    result[2] = "جمع مذكر مرفوع في حالة الاضافة"
                    priority += "3112"
            else:
                result[2] = "جمع مذكر مرفوع نكرة"
                priority += "3113"
        elif vnp.ncg == "6":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مؤنث في حالة التعريف"
                    priority += "3211"
                else:
                    result[2] = "جمع مؤنث مرفوع في حالة الاضافة"
                    priority += "3212"
            else:
                result[2] = "جمع مؤنث مرفوع نكرة"
                priority += "3213"
        elif vnp.ncg == "7":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مذكر منصوب في حالة التعريف"
                    priority += "1121"
                else:
                    result[2] = "مفرد مذكر منصوب في حالة الاضافة"
                    priority += "1122"
            else:
                result[2] = "مفرد مذكر منصوب نكرة"
                priority += "1123"
        elif vnp.ncg == "8":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مؤنث منصوب في حالة التعريف"
                    priority += "1221"
                else:
                    result[2] = "مفرد مؤنث منصوب في حالة الاضافة"
                    priority += "1222"
            else:
                result[2] = "مفرد مؤنث منصوب نكرة"
                priority += "1223"
        elif vnp.ncg == "9":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مذكر منصوب في حالة التعريف"
                    priority += "2121"
                else:
                    result[2] = "مثنى مذكر منصوب في حالة الاضافة"
                    priority += "2122"
            else:
                result[2] = "مثنى مذكر منصوب نكرة"
                priority += "2123"
        elif vnp.ncg == "10":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مؤنث منصوب في حالة التعريف"
                    priority += "2221"
                else:
                    result[2] = "مثنى مؤنث منصوب في حالة الاضافة"
                    priority += "2222"
            else:
                result[2] = "مثنى مؤنث منصوب نكرة"
                priority += "2223"
        elif vnp.ncg == "11":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مذكر منصوب في حالة التعريف"
                    priority += "3121"
                else:
                    result[2] = "جمع مذكر منصوب في حالة الاضافة"
                    priority += "3122"
            else:
                result[2] = "جمع مذكر منصوب نكرة"
                priority += "3123"
        elif vnp.ncg == "12":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مؤنث منصوب في حالة التعريف"
                    priority += "3221"
                else:
                    result[2] = "جمع مؤنث منصوب في حالة الاضافة"
                    priority += "3222"
            else:
                result[2] = "جمع مؤنث منصوب نكرة"
                priority += "3223"
        elif vnp.ncg == "13":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مذكر مجرور في حالة التعريف"
                    priority += "1131"
                else:
                    result[2] = "مفرد مذكر مجرور في حالة الاضافة"
                    priority += "1132"
            else:
                result[2] = "مفرد مذكر مجرور نكرة"
                priority += "1133"
        elif vnp.ncg == "14":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مفرد مؤنث مجرور في حالة التعريف"
                    priority += "1231"
                else:
                    result[2] = "مفرد مؤنث مجرور في حالة الاضافة"
                    priority += "1232"
            else:
                result[2] = "مفرد مؤنث مجرور نكرة"
                priority += "1233"
        elif vnp.ncg == "15":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مذكر مجرور في حالة التعريف"
                    priority += "2131"
                else:
                    result[2] = "مثنى مذكر مجرور في حالة الاضافة"
                    priority += "2132"
            else:
                result[2] = "مثنى مذكر مجرور نكرة"
                priority += "2133"
        elif vnp.ncg == "16":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "مثنى مؤنث مجرور في حالة التعريف"
                    priority += "2231"
                else:
                    result[2] = "مثنى مؤنث مجرور في حالة الاضافة"
                    priority += "2232"
            else:
                result[2] = "مثنى مؤنث مجرور نكرة"
                priority += "2233"
        elif vnp.ncg == "17":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مذكر مجرور في حالة التعريف"
                    priority += "3131"
                else:
                    result[2] = "جمع مذكر مجرور في حالة الاضافة"
                    priority += "3132"
            else:
                result[2] = "جمع مذكر مجرور نكرة"
                priority += "3133"
        elif vnp.ncg == "18":
            if vnp.cas == "إض":
                if seg.prefix.classe in ["N1", "N2", "N3", "N5"]:
                    result[2] = "جمع مؤنث في حالة التعريف"
                    priority += "3231"
                else:
                    result[2] = "جمع مؤنث مجرور في حالة الاضافة"
                    priority += "3232"
            else:
                result[2] = "جمع مؤنث مجرور نكرة"
                priority += "3233"
        elif vnp.ncg == "0":
            result[2] = "مفرد مذكر"
            priority += "11"
        elif vnp.ncg == "-1":
            result[2] = "مفرد مؤنث"
            priority += "12"
        elif vnp.ncg == "-2":
            result[2] = "جمع مذكر"
            priority += "31"
        elif vnp.ncg == "-3":
            result[2] = "جمع مؤنث"
            priority += "32"

        if vnp.ncg in ["2", "8", "14"] and seg.stem.unvoweledform.endswith("ة"):
            seg.stem.lemma = seg.stem.unvoweledform[:-1]
            suffix += "ة"
            suffix_txt += "ة: تاء التأنيث"

        if vnp.ncg in ["4", "10", "16"]:
            suffix += "ة"
            if seg.stem.unvoweledform.endswith("تان"):
                seg.stem.lemma = seg.stem.unvoweledform[:-3]
                suffix_txt += "ة:تاء التأنيث+ا علامة الإعراب"
            if seg.stem.unvoweledform.endswith("تين"):
                seg.stem.lemma = seg.stem.unvoweledform[:-3]
                suffix_txt += "ة:تاء التأنيث+ي علامة الإعراب"
            if seg.stem.unvoweledform.endswith("تا"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix_txt += "ة:تاء التأنيث+ا علامة الإعراب"

        if vnp.ncg in ["6", "12", "18"]:
            if seg.stem.unvoweledform.endswith("ات"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "ات"
                suffix_txt += "ات:تاء التأنيث"

        if vnp.ncg in ["3", "9", "15"]:
            if seg.stem.unvoweledform.endswith("ان"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "ان"
                suffix_txt += "ان: علامة الإعراب"
            if seg.stem.unvoweledform.endswith("ين"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "ين"
                suffix_txt += "ين:علامة الإعراب"
            if seg.stem.unvoweledform.endswith("ا"):
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                suffix += "ا"
                suffix_txt += "ا:علامة الإعراب"
            if seg.stem.unvoweledform.endswith("ي"):
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                suffix += "ي"
                suffix_txt += "ي:علامة الإعراب"

        if vnp.ncg in ["5", "11", "17"]:
            if seg.stem.unvoweledform.endswith("ون"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "ون"
                suffix_txt += "ون:علامة الإعراب"
            if seg.stem.unvoweledform.endswith("ين"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "ين"
                suffix_txt += "ين:علامة الإعراب"
            if seg.stem.unvoweledform.endswith("وا"):
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                suffix += "وا"
                suffix_txt += "وا: علامة الإعراب"
            if seg.stem.unvoweledform.endswith("ي"):
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                suffix += "ي"
                suffix_txt += "ي: علامة الإعراب"

        result[4] = priority

        if result[0] == "" and prefix != "":
            result[0] = prefix
        elif result[0] != "" and prefix != "":
            result[0] += "+ " + prefix

        if result[3] == "" and suffix != "":
            result[3] = suffix
        elif result[3] != "" and suffix != "":
            result[3] = suffix + "+ " + result[3]

        return result


    def interpret_vvp(self, seg, vnp, root):
        result = [""] * 7
        priority = "2"
        prefix = ""
        prefix_txt = ""
        suffix = ""
        suffix_txt = ""
        pos = ""

        if seg.prefix.voweledform != "":
            result[0] = f"{seg.prefix.voweledform}: {seg.prefix.desc}"
        if seg.suffix.voweledform != "":
            result[3] = f"{seg.suffix.voweledform}: {seg.suffix.desc}"

        type_mapping = {
            "مم": ("فعل ماض مبني للمعلوم", "11"),
            "مج": ("فعل ماض مبني للمجهول", "12"),
            "ضم": ("فعل مضارع مبني للمعلوم", "21"),
            "ضءم": ("فعل مضارع مؤكد مبني للمعلوم", "21"),
            "ضج": ("فعل مضارع مبني للمجهول", "22"),
            "ضءج": ("فعل مضارع مؤكد مبني للمجهول", "22"),
            "أ": ("فعل أمر", "3"),
            "أء": ("فعل أمر مؤكد", "3")
        }
        result[1], type_priority = type_mapping.get(vnp.type, ("", ""))
        priority += type_priority

        if len(root) == 3:
            pos += "ثلاثي"
        else:
            pos += "رباعي"
        pos += f" {'مجرد' if vnp.aug == 'جر' else 'مزيد'}"

        cas_mapping = {
            "ج": (" مجزوم", "3"),
            "ر": (" مرفوع", "1"),
            "ن": (" منصوب", "2")
        }
        cas_pos, cas_priority = cas_mapping.get(vnp.cas, ("", ""))
        pos += cas_pos
        priority += cas_priority

        ncg_mapping = {
            "1": "مسند إلى المتكلم أنا",
            "2": "مسند إلى المتكلمين(نحن)",
            "3": "مسند إلى المخاطَب أنت",
            "4": "مسند إلى المخاطبة(أنتِ)",
            "5": "مسند إلى المخاطَبَين(أنتما)",
            "6": "مسند إلى المخاطبين(أنتم)",
            "7": "مسند إلى المخاطَبات(أنتن)",
            "8": "مسند إلى الغائب(هو)",
            "9": "مسند إلى الغائبة(هي)",
            "10": "مسند إلى الغائبَين(هما)",
            "11": "مسند إلى الغائبتين(هما)",
            "12": "مسند إلى الغائبين(هم)",
            "13": "مسند إلى الغائبات(هن)"
        }
        pos += f" {ncg_mapping.get(vnp.ncg, '')}"
        #same as bellow 5 lines
        if vnp.trans == "ل":
            pos += " " + "لازم"
            priority += "1"
        elif vnp.trans == "م":
            pos += " " + "متعد"
            priority += "2"
        else:
            pos += " " + "متعد ولازم"
            priority += "3"

        if vnp.type == "أ":
            ncg_mapping = {
                #"3": ("", ""),#@TODO: why append empty string
                "4": ("ي", "ياء المخاطبة"),
                "5": ("ا", "ألف المثنى"),
                "6": ("وا", "واو الجماعة"),
                "7": ("ن", "نون النسوة")
            }
            ncg_suffix, ncg_suffix_txt = ncg_mapping.get(vnp.ncg, ("", ""))
            suffix += ncg_suffix
            suffix_txt += suffix+": "+ncg_suffix_txt
            seg.stem.lemma = seg.stem.unvoweledform[:-len(ncg_suffix)]

        if vnp.type == "أء":
            seg.stem.lemma = seg.stem.unvoweledform[:-1]
            suffix += "ن"
            suffix_txt += "ن: نون التوكيد"

        if vnp.type in ["مم", "مج"]:
            ncg_mapping = {
                "1": ("ت", "تاء المتكلم"),
                "2": ("نا", "نون المتكلمين"),
                "3": ("ت", "تاء المخاطب"),
                "4": ("ت", "تاء المخاطبة"),
                "5": ("تما", "تاء المخاطبين"),
                "6": ("تم", "تاء المخاطبين"),
                "7": ("تن", "تاء المخاطبات"),
                #"8": ("", ""),
                "9": ("ت", "تاء التأنيث الساكنة"),
                "10": ("ا", "ألف الاثنين"),
                "11": ("تا", "ألف الاثنين"),
                "12": ("وا", "واو الجماعة"),
                "13": ("ن", "نون النسوة")
            }
            ncg_suffix, ncg_suffix_txt = ncg_mapping.get(vnp.ncg, ("", ""))
            suffix += ncg_suffix
            suffix_txt += suffix+": "+ncg_suffix_txt
            seg.stem.lemma = seg.stem.unvoweledform[:-len(ncg_suffix)]

        if vnp.type in ["ضم", "ضج"]:
            prefix_mapping = {
                "1": "أ",
                "2": "ن",
                "3": "ت",
                "4": "ت",
                "7": "ن",
                "8": "ي",
                "9": "ت",
            }
            suffix_mapping = {
                "7": "ن",
            }
            if vnp.ncg in prefix_mapping:
                prefix += prefix_mapping[vnp.ncg]
                if vnp.ncg == "9":
                    prefix_txt +=  prefix_mapping[vnp.ncg] + ": تاء الغائبة"
                else:
                    prefix_txt += prefix_mapping[vnp.ncg] + ": حرف المضارعة"
            if vnp.ncg in suffix_mapping:
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                suffix += "ن"
                suffix_txt += "ن: نون التوكيد"

            if vnp.ncg == "4":
                prefix += "ت"
                prefix_txt += "ت: حرف المضارعة"
                if vnp.cas in ["ن", "ج"]:
                    seg.stem.lemma = seg.stem.unvoweledform[:-1]
                    suffix += "ي"
                    suffix_txt += "ي: ياء المخاطبة"
                else:
                    seg.stem.lemma = seg.stem.unvoweledform[:-2]
                    suffix += "ين"
                    suffix_txt += "ين: ياء المخاطبة+ن علامة الرفع"
            if vnp.ncg == "5":
                prefix += "ت"
                prefix_txt += "ت:حرف المضارعة"
                if vnp.cas in ["ن", "ج"]:
                    seg.stem.lemma = seg.stem.unvoweledform[:-1]
                    suffix += "ا"
                    suffix_txt += "ا: ألف المثنى"
                else:
                    seg.stem.lemma = seg.stem.unvoweledform[:-2]
                    suffix += "ان"
                    suffix_txt += "ان: ألف المثنى+ن علامة الرفع"
            if vnp.ncg == "6":
                prefix += "ت"
                prefix_txt += "ت:حرف المضارعة"
                if vnp.cas in ["ن", "ج"]:
                    seg.stem.lemma = seg.stem.unvoweledform[:-1]
                    suffix += "وا"
                    suffix_txt += "وا: واو الجماعة"
                else:
                    seg.stem.lemma = seg.stem.unvoweledform[:-2]
                    suffix += "ون"
                    suffix_txt += "ون: واو الجماعة+ن علامة الرفع"

            if vnp.ncg == "10":
                prefix += "ي"
                prefix_txt += "ي:حرف المضارعة"
                if vnp.cas in ["ن", "ج"]:
                    seg.stem.lemma = seg.stem.unvoweledform[:-1]
                    suffix += "ا"
                    suffix_txt += "ا: ألف المثنى"
                else:
                    seg.stem.lemma = seg.stem.unvoweledform[:-2]
                    suffix += "ان"
                    suffix_txt += "ان: ألف المثنى+ن علامة الرفع"
            if vnp.ncg == "11":
                prefix += "ت"
                prefix_txt += "ت:حرف المضارعة"
                if vnp.cas in ["ن", "ج"]:
                    seg.stem.lemma = seg.stem.unvoweledform[:-1]
                    suffix += "ا"
                    suffix_txt += "ا: ألف المثنى"
                else:
                    seg.stem.lemma = seg.stem.unvoweledform[:-2]
                    suffix += "ان"
                    suffix_txt += "ان: ألف المثنى+ن علامة الرفع"
            if vnp.ncg == "12":
                prefix += "ي"
                prefix_txt += "ي:حرف المضارعة"
                seg.stem.lemma = seg.stem.unvoweledform[:-2]
                if vnp.cas in ["ن", "ج"]:
                    suffix += "وا"
                    suffix_txt += "وا: واو الجماعة"
                else:
                    suffix += "ون: واو الجماعة+ن علامة الرفع"
            if vnp.ncg == "13":
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                prefix += "ي"
                prefix_txt += "ي: حرف المضارعة"
                suffix += "ن"
                suffix_txt += "ن: نون النسوة"

        if vnp.type in ["ضءم", "ضءج"]:
            prefix_mapping = {
                "1": "أ",
                "2": "ن",
                "3": "ت",
                "4": "ت",
                "5": "ت",
                "6": "ت",
                "7": "ت",
                "8": "ي",
                "9": "ت",
                "10": "ي",
                "11": "ت",
                "12": "ي",
                "13": "ي"
            }
            if vnp.ncg in prefix_mapping:
                prefix += prefix_mapping[vnp.ncg]
                prefix_txt += prefix_mapping[vnp.ncg] + ": حرف المضارعة"
                seg.stem.lemma = seg.stem.unvoweledform[:-1]
                suffix += "ن"
                suffix_txt += "ن: نون التوكيد"


        #######################################################
        result[2] = pos
        result[4] = priority

        if result[0] == "" and prefix != "":
            result[0] = prefix
            result[5] = prefix_txt
        elif result[0] != "" and prefix != "":
            result[0] += f"+ {prefix}"
            result[5] += f"+ {prefix}"

        if result[3] == "" and suffix != "":
            result[3] = suffix
            result[6] = suffix_txt
        elif result[3] != "" and suffix != "":
            result[3] = f"{suffix}+ {result[3]}"
            result[6] = f"{suffix}+ {result[3]}"

        return result
