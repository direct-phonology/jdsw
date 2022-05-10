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
    (?P<initial>[^_])       # initial/onset
    (?P<rime>[^_])          # rime/tone
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
    (?P<anno>[^_])          # sounds "the same as" this character
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

# chapters we don't care about using: paratextual material, notes, etc.
BLACKLIST = (
    "KR1g0003_000",  # introduction
    "KR1g0003_001",  # 序録
    "KR1g0003_031",  # notes
    "KR1g0003_032",  # notes
    "KR1g0003_033",  # notes
)

# indicator for missing data/annotation
BLANK = "_"

# artifacts in kanseki repository text
MODE_HEADER = re.compile(r"# -\*- mode: .+; -\*-\n")
META_HEADER = re.compile(r"#\+\w+: .+\n")
LINE_BREAK = re.compile(r"<pb:(?:.+)>¶\n")
ANNOTATION = re.compile(r"\((.+?)\)")
