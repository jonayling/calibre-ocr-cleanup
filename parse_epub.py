
from ebooklib import epub
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
import re
import operator

black_list = {
    "ofthe", "inthe", "andthe", "hehad", "hewas", "itwas", "fromthe", "forthe", "atthe", "tothe", "hewrote", "forthe",
    "wasnot", "theother", "andon", "iam", "andsome", "andso", "thegeneral", "hadbeen", "anda", "wasn", "itis", "onthe",
    "wherethe", "thehigh", "thenorth", "aplace", "therewas", "publicschool", "thehouse", "toget", "theantarctic",
    "itin", "thebarrier", "tobe", "theyhad", "whenthe", "theywere", "newzealand", "andthey", "thefirst", "hada", "theexpedition",
    "theothers", "beforethe", "hadhad", "thatthe", "thequestion", "theresult", "turnedout", "ofhis", "whilethey", "foundthe",
    "afterthe", "formany", "shouldhave", "wasstill", "thesecond", "upwith", "withhim", "cherrywrote", "andwas", "isthe", "withthe"
}

white_list = {
    "antarcticans", "sledged", "hadn", "wasn", "hasn"
}

spell = SpellChecker(local_dictionary="en3.json")

def find_gapped_correct(word):
    for i in range(1, len(word)):
        gapped_left = word[:i]
        gapped_right = word[i:]

        if not spell.unknown([gapped_left, gapped_right]):
            yield (gapped_left, gapped_right)

def couple_score(word1, word2):
    return spell.word_frequency[word1] + spell.word_frequency[word2]

def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i+1)

def replace_retain_case(text, error, rep_left, rep_right):
    gap_pos = error.rfind(rep_right)

    i = text.lower().find(error.lower())
    if i < 0: return text

    original = text[i:i+len(error)]

    cases = [c.isupper() for c in original]
    cases.insert(gap_pos, False)

    replaced = ''.join([c if not cases[ind] else c.upper() for ind, c in enumerate(rep_left + " " + rep_right)])

    # Actually replace in the text
    updated = re.sub(error, replaced, text, flags=re.IGNORECASE)

    return updated

def construct_whitelist(xhtml, threshold):
    soup = BeautifulSoup(xhtml, features="lxml")
    complete_text = ' '.join([p.text for p in soup.find_all('p')])
    complete_text_lower = complete_text.lower()
    words = spell.split_words(complete_text)

    # Find the set of misspelled words
    misspelled = spell.unknown(words)
    # Count the occurrence of each word
    occurrence = {ms: len(re.findall(r'\b'+ ms + r'\b', complete_text_lower, re.IGNORECASE)) for ms in misspelled}

    occurrence = sorted(occurrence.items(), key=operator.itemgetter(1), reverse=True)
    whitelist_terms = {k for k,v in occurrence[:threshold]}
    whitelist_terms = whitelist_terms - black_list
    whitelist_terms.update(white_list)

    return whitelist_terms


book = epub.read_epub('mary.epub')

for item in range(2, 3):
    print('Processing item {0}...'.format(item))

    xhtml = book.items[item].content
    xhtml = xhtml.decode('utf-8')

    whitelist = construct_whitelist(xhtml, 30)

    soup = BeautifulSoup(xhtml, features="lxml")

    for p in soup.find_all('p'):
        if not p or not p.string: continue

        text_original = p.text
        text = p.text

        words = spell.split_words(text)
        misspelled = spell.unknown(words)
        for mis in misspelled:
            if mis in whitelist: continue

            # Find any candidates that are equivalent to the mispelled word with a space in it
            gapped_correct = list(find_gapped_correct(mis))


            if any(gapped_correct):
                scores = {couple_score(l,r): (l,r) for l,r in gapped_correct }
                best_match = scores[max(scores.keys())]

                text = replace_retain_case(text, mis, best_match[0], best_match[1])

        p.string.replace_with(text)

    complete_text = ' '.join([p.text for p in soup.find_all('p')])
    book.items[item].set_content(soup.prettify().encode("utf-8"))

epub.write_epub("mary_processed.epub", book)
