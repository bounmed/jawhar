# Create a list of Arabic basic letters
arabic_basic_letters = ['ء','ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'و', 'ي']

# Print the list of Arabic basic letters
for char1 in arabic_basic_letters:
    for char2 in arabic_basic_letters:
        for char3 in arabic_basic_letters:
            word = char1+char2+char3
            print(word)
