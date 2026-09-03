import re

class Tokenizer:
    def __init__(self, text_to_be_analyzed):
        input_text = text_to_be_analyzed.strip()
        input_text = input_text.replace("ـ", "")
        input_text = re.sub(r"([^\sَءةًٌُِإٍّْئؤآأابتثجحخدذرزسشصضطظعغفقكلمىنهوي])", " ", input_text)
        # input_text = re.sub("\\s+", " ", input_text)

        #self.words = input_text.split("\\s+")
        self.words = input_text.split()  # Split by spaces
        self.nbr_words = len(self.words)
        self.normalized_tokens = []
        self.unvoweled_tokens = []
        self.remove_stop_words = False
        if len(self.words) > 2:
            self.remove_stop_words = True

        for word in self.words:
            normalized_word = word
            unvoweled_word = re.sub("[ًٌٍَُِّْ]", "", normalized_word)
            if unvoweled_word not in self.unvoweled_tokens:
                # normalized_tokens keeps the original diacritics (if any) for
                # compatibility-checking inside the Analyzer.
                # unvoweled_tokens strips diacritics for pattern/root matching.
                self.normalized_tokens.append(normalized_word)
                self.unvoweled_tokens.append(unvoweled_word)

    def get_normalized_tokens(self):
        return self.normalized_tokens

    def get_unvoweled_tokens(self):
        return self.unvoweled_tokens

    def get_words(self):
        return self.words
