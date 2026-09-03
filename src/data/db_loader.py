import os
import json

from ..models.prefix import Prefix
from ..models.suffix import Suffix
from ..models.unvoweled_pattern import UnvoweledPattern
from ..models.voweled_nominal_patterns_list import VoweledNominalPatternsList
from ..models.voweled_nominal_pattern import VoweledNominalPattern
from ..models.voweled_verbal_patterns_list import VoweledVerbalPatternsList
from ..models.voweled_verbal_pattern import VoweledVerbalPattern
from ..models.tool_word import ToolWord
from ..models.root import Root
from ..models.proper_noun import ProperNoun
from ..models.exceptional_word import ExceptionalWord

class DbLoader:
    def __init__(self):
        # Base directory for all file paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def LoadPrefixes(self):
        prefixes = []
        try:
            with open(os.path.join(self.base_dir, "db/prefixes.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    prefix = Prefix(item['unvoweledform'], item['voweledform'],
                                     item['desc'], item['classe'])
                    prefixes.append(prefix)
        except Exception as ex:
            print("Exception: ", ex)
        return prefixes

    def LoadSuffixes(self):
        suffixes = []
        try:
            with open(os.path.join(self.base_dir, "db/suffixes.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    suffix = Suffix(item.get('unvoweledform', ''), item.get('voweledform', ''),
                                     item.get('desc', ''), item.get('classe', ''))
                    suffixes.append(suffix)
        except Exception as ex:
            print(ex)
        return suffixes

    def LoadUnvoweledNominalPatterns(self, length):
        patterns = []
        try:
            if 2 <= length <= 9:
                path = os.path.join(self.base_dir, "db/nouns/patterns/Unvoweled/UnvoweledNominalPatterns" + str(length) + ".json")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        pattern = UnvoweledPattern(item.get('value'), item.get('rules'), item.get('ids'))
                        patterns.append(pattern)
        except Exception as ex:
            print(ex)
        return patterns

    def LoadUnvoweledVerbalPatterns(self, length):
        patterns = []
        try:
            if 2 <= length <= 9:
                path = os.path.join(self.base_dir, "db/verbs/patterns/Unvoweled/UnvoweledVerbalPatterns" + str(length) + ".json")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        pattern = UnvoweledPattern(item.get('value'), item.get('rules'), item.get('ids'))
                        patterns.append(pattern)
        except Exception as ex:
            print(ex)
        return patterns

    def LoadVoweledNominalPatterns(self, length):
        patterns = []
        try:
            if 2 <= length <= 9:
                path = os.path.join(self.base_dir, "db/nouns/patterns/Voweled/VoweledNominalPatterns" + str(length) + ".json")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        pattern = VoweledNominalPattern(item.get('id'), item.get('diac'),
                                                         item.get('canonic'), item.get('type'),
                                                         item.get('cas'), item.get('ncg'))
                        patterns.append(pattern)
        except Exception as ex:
            print(ex)
        return patterns

    def LoadVoweledVerbalPatterns(self, length):
        patterns = []
        try:
            if 2 <= length <= 9:
                path = os.path.join(self.base_dir, "db/verbs/patterns/Voweled/VoweledVerbalPatterns" + str(length) + ".json")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        pattern = VoweledVerbalPattern(item.get('id'), item.get('diac'),
                                                        item.get('canonic'), item.get('type'),
                                                        item.get('aug'), item.get('cas'),
                                                        item.get('ncg'), item.get('trans'))
                        patterns.append(pattern)
        except Exception as ex:
            print(ex)
        return patterns

    def LoadNominalRootsByFirstChar(self, fc):
        roots = []
        try:
            path = os.path.join(self.base_dir, "db/nouns/roots2/" + fc + ".json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    root_obj = Root(item.get('val'), item.get('vect'))
                    roots.append(root_obj)
        except Exception as ex:
            print(ex)
        return roots

    def LoadVerbalRootsByFirstChar(self, fc):
        roots = []
        try:
            path = os.path.join(self.base_dir, "db/verbs/roots2/" + fc + ".json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    root_obj = Root(item.get('val'), item.get('vect'))
                    roots.append(root_obj)
        except Exception as ex:
            print(ex)

        return roots

    def LoadToolWords(self):
        toolwords = []
        try:
            path = os.path.join(self.base_dir, "db/specialwords/toolwords.json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    toolword = ToolWord(item.get('unvoweledform'), item.get('voweledform'),
                                         item.get('type'), item.get('prefixclass'),
                                         item.get('suffixclass'), item.get('priority'))
                    toolwords.append(toolword)
        except Exception as ex:
            print(ex)
        return toolwords

    def LoadProperNouns(self):
        propernouns = {}
        try:
            path = os.path.join(self.base_dir, "db/specialwords/propernouns.json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    propernoun = ProperNoun(item.get('unvoweledform'), item.get('voweledform'),
                                             item.get('type'))
                    propernouns[item.get('unvoweledform')] = propernoun
        except Exception as ex:
            print(ex)
        return propernouns

    def LoadExceptionalWords(self):
        exceptionalwords = []
        try:
            path = os.path.join(self.base_dir, "db/specialwords/exceptionalwords.json")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    exceptionalword = ExceptionalWord(item.get('unvoweledform'),
                                                       item.get('voweledform'),
                                                       item.get('prefix'),
                                                       item.get('stem'),
                                                       item.get('type'),
                                                       item.get('suffix'))
                    exceptionalwords.append(exceptionalword)
        except Exception as ex:
            print(ex)
        return exceptionalwords

    def LoadAllRoots2(self) :
        roots = {}
        try:
            allRoots2_path = os.path.join(self.base_dir, "db/AllRoots2.txt")
            with open(allRoots2_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        roots[parts[0]] = parts[1]
        except Exception as ex:
            print(ex)

        return roots

    def LoadAllRoots1(self) :
        roots = {}
        try:
            allRoots1_path = os.path.join(self.base_dir, "db/AllRoots1.txt")
            with open(allRoots1_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        roots[parts[0]] = parts[1]
        except Exception as ex:
            print(ex)

        return roots
