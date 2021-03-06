import re

# fmt: off
# any type of annotation (character paired with paratext)
ANNOTATION = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (?P<anno>[^_]+?)        # annotation
    $
""", re.VERBOSE | re.MULTILINE)

# fanqie annotations (character that reads like a combination of two characters)
FANQIE = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (如字)?[徐|又]?
    (?P<initial>[^_])       # character with same initial
    (?P<rime>[^_])          # character with same rime
    反
    [下注後同與也及專大]*
    $
""", re.VERBOSE | re.MULTILINE)

# "yin" annotations (character that reads the same as another character)
YIN = re.compile(r"""
    ^
    (?P<char>.)             # character being annotated
    \t
    (如字)?[徐|又]?
    音
    (?P<anno>[^_])          # initial and rime are the same as this character
    [下注後同與也及專大]*
    $
""", re.VERBOSE | re.MULTILINE)

# special non-unicode entities in kanseki repository text
KR_ENTITY = re.compile(r"""
    (
    &(?P<id>KR\d+);     # entity with a code/id, e.g. &KR0001;
    |
    (?P<combo>\[.+?\])  # entity defined as a combo, e.g. [阿-可+利]
    )
""", re.VERBOSE)
# fmt: on

# case where there's no annotation for a character
EMPTY_ANNO = re.compile(r"^(?P<char>.)\t_$", re.MULTILINE)

# types of annotations we're able to transform automatically
WHITELIST = (FANQIE, YIN)

# indicator for missing data/annotation
BLANK = "_"

# org-mode header that indicates the text mode, ex.:
# "# -*- mode: mandoku-view -*-"
MODE_HEADER = re.compile(r"^# -\*- mode: .+;? -\*-$", re.MULTILINE)

# indicators of page breaks in the text, ex.:
# "<pb:KR1d0001_tls_001-1a>¶"
PAGE_BREAK = re.compile(r"<pb:(?:.+)>¶?")

# org-mode headers in key:value format, ex.:
# "#+TITLE: 周禮"
# "#+PROPERTY: BASEEDITION tls"
META_HEADER = re.compile(
    r"""
    ^\#\+
    (?P<key>\w+):\s
    (?P<value>.+)
    $
""",
    re.VERBOSE | re.MULTILINE,
)

# headers within a file that indicate the current chapter, ex.:
# "** 1 天官冢宰"
# "** 19 《子張篇第十九》"
CHAPTER_HEADER = re.compile(
    r"""
    ^[*]{2}\s               
    (?P<number>\d+)\s
    《?(?P<title>.+)》?    # strips 《》
    $
""",
    re.VERBOSE | re.MULTILINE,
)

# in-text numbers in a file that identify the current paragraph, ex.:
# "1.46.內小臣掌王后之命，¶"
PARAGRAPH_NUMBER = re.compile(
    r"""
    ^(?P<number>        # always at start of a line
    \d+(?:[.．]\d+)+    # 1, 1.2, 10.8.4, etc.
    ).?                 # ignore trailing period
""",
    re.VERBOSE | re.MULTILINE,
)

# comments on provenance, dating, etc. ex.:
# "# dating: 6200"
COMMENT = re.compile(
    r"""
    ^\#\s
    (?P<key>\w+):\s     # dating:, src:, etc.
    (?P<vals>.+)        # can be semicolon-separated, multiple values
    $
""",
    re.VERBOSE | re.MULTILINE,
)

# a sequence of lines terminating in a full stop, ex.:
# "賊器不入宮，¶
#  奇服怪民不入宮。¶"
SENTENCE = re.compile(r"^(?:\S+\n)*?\S+[。！？]$", re.MULTILINE)

# text that is identified as a commentary or note by parentheses, ex.:
# "稱妣(必履/反)"
ANNOTATION = re.compile(r"\((.+?)\)")

# y- and z-variant indicators in Unihan
KSEMVAR_THREE = re.compile(r"U\+(\w+)<(?:k\w+,?){3}")  # all three dicts agree
KSEMVAR_TWO = re.compile(r"U\+(\w+)<(?:k\w+,?){2}")  # two dicts agree
KSEMVAR_ONE = re.compile(r"U\+(\w+)<k\w+")  # use any dict
KZVAR = re.compile(r"U\+(\w+)")  # z-variant
