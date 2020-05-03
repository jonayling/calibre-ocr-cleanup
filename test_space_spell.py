from spellchecker import SpellChecker

spell = SpellChecker(local_dictionary="en3.json")

def find_gapped_correct(word):
    for i in range(1, len(word)):
        gapped_left = word[:i]
        gapped_right = word[i:]

        if not spell.unknown([gapped_left, gapped_right]):
            yield (gapped_left, gapped_right)


foo = spell.unknown(["thathe"])

for mis in foo:
    for w in find_gapped_correct(mis):
        print(w)
