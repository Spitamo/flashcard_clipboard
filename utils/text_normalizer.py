import re
from wordfreq import zipf_frequency

Word_regex = re.compile(r"^[a-z]+(?:['-][a-z]+)*$")

Forbidden_patterns =  [
    re.compile(r"https?://", re.I),
    re.compile(r"www\.", re.I),
    re.compile(r"@"),
    re.compile(r"\d"),
    re.compile(r"/"),
    re.compile(r"\.")
]


def normalize_text(text : str):
   if text is None:
      return False

   return text.strip().lower()

def is_valid_english_word(text : str):

   word = normalize_text(text)

   if not word:
      return False
      

   for pattern in Forbidden_patterns:
      if pattern.search(word):
         return False

   if not Word_regex.fullmatch(word):
      return False

   if '-' in word:
      text = word.split('-')
      for item in text:
         if zipf_frequency(item, "en") < 3:
            return False


   #zipf scale
   score = zipf_frequency(word, "en")

   #initial Threshold
   return score >= 2.3



   
# test_list = ['a', 'adequate', '$$#bool', 'bool', '']

# print([item for item in test_list if is_valid_english_word(item)])

