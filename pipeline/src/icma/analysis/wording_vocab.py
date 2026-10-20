"""Words and patterns the wording rules recognize, all in normalized text (icma.arabic).

Each pattern matches at a word start; `END` keeps a match from ending inside a word.
"""

import re


def words(text: str) -> frozenset[str]:
    return frozenset(text.split())


END = r"(?= |$)"
_EULOGY = (
    r"(?: (?:صلي ?الله ?(?:تعالي )?عليه(?: و(?:علي )?اله)?(?: وسلم)?"
    r"|عليه السلام|عليه الصلاه والسلام))?"
)
PROPHET = rf"(?:رسول الله|النبي|نبي الله){_EULOGY}"

# Skipped between the last narrator and the matn.
HONORIFIC = re.compile(r"(?:رضي الله(?: تعالي)? عن(?:ه|هما|ها|هم)|رحمه الله(?: تعالي)?)" + END)
EPITHET = re.compile(rf"(?:زوج|صاحب|مولي|خادم|من اصحاب) {PROPHET}" + END)
GLOSS = re.compile(rf"و[^ ]+(?: [^ ]+){{0,10}}? (?=(?:ان|انه) {PROPHET})")
LINK = re.compile(
    rf"(?:(?:قال|فقال|وقال|انه قال|انه|ان|عن|يرفعه|سمعت|يقول) )*{PROPHET}"
    rf"(?P<verb> (?:قال|فقال|يقول|كان يقول|انه قال|انه))?" + END
)
SAYS = re.compile(
    r"(?:قال|انه قال|قالت|انها قالت|قالوا|يقول|اخبرته|اخبره|حدثته|حدثه|انه سمع)" + END
)

# Formulas that point at another chain's wording.
LEAD = re.compile(r"(?:يعني|ثم)" + END)
VERB = re.compile(r"(?:قال )?(?:ف|و)?(?:ذكر|ساق)(?P<obj>ه)?" + END)
FORMULA_SOURCES: tuple[tuple[str, str, bool], ...] = (
    # (pattern, kind, takes a name: "باسناد يحيي", "مثل حديث ابن جعفر")
    (r"(?:ب|و)?(?:هذا|ذلك|هذين) (?:الاسناد|الاسنادين)(?: نفسه)?", "isnad", False),
    (r"(?:ب|و)?اسناده(?:ما|م)?(?: نفسه)?", "isnad", False),
    (r"بالاسناد|به", "isnad", False),
    (r"(?:ب|و)?(?:مثل )?اسناد", "isnad", True),
    (r"(?:ب)?مثل حديث", "same", True),
    (r"(?:ب|في )?مثل(?:ه|ها|هما)(?: سواء)?|(?:ب)?مثل ذلك", "same", False),
    (r"(?:ب)?نحو حديث", "similar", True),
    (r"(?:ب)?نحو(?:ه|ها|هما)|(?:ب)?نحوا منه|(?:ب)?نحو ذلك|(?:ب)?نحو منه", "similar", False),
    (r"(?:ب)?معني حديث", "meaning", True),
    (r"(?:ب|و|في )?معنا(?:ه|ها|هما)|بمعني ذلك", "meaning", False),
    (r"(?:ب|في )حديث", "reference", True),
    (
        r"(?:ب)?(?:هذا|ذلك) الحديث|بهذا|بذلك|بحديثه|بطوله|بقصته|الحديث(?: بطوله)?",
        "reference",
        False,
    ),
)
NAME_STOP = words(
    "غير الا وزاد زاد قال وقال فقال وفيه فيه في حديثه مثله بمثله نحوه بنحوه معناه بمعناه ومعناه"
)
NOT_NAMES = words("حسن صحيح غريب منكر مرسل الحديث حديث")
# Introduces the words quoted for a chain after a formula: "غير أن في حديثهما ...".
PARTIAL_LEAD = re.compile(
    r"(?:(?:غير|الا) ان(?:ه)?(?: قال)?(?: في حديثه(?:ما|م)?)?(?: قال)?|وزاد(?: فيه)?|زاد(?: فيه)?"
    r"|وقالا|قالا|وقالوا|قالوا|وقال|قال)" + END
)
# Ends a quoted start of a matn: "ثم ذكر مثله", "وذكر الحديث", a final "الحديث".
TRAILING = re.compile(
    r"(?:^| )(?=(?:ثم )?(?:ف|و)?(?:ذكر|ساق) (?:(?:ب)?(?:مثل|نحو|معني) حديث|الحديث|مثله|نحوه|معناه))"
    r"|(?:^| )(?=الحديث$)"
)

# Ends a wording.
ISNAD_VERB = re.compile(
    r"(?:^| )(?=(?:(?:و)?(?:حدثنا|حدثني|حدثناه|حدثنيه|اخبرنا|اخبرني|اخبرناه|انبانا|ثنا|قثنا|ح)"
    r"|ونا|فحدثنيه|فحدثناه|فاخبرنيه)" + END + ")"
)
COMMENTARY = re.compile(
    r"(?:^| )(?=(?:"
    r"قال (?:ابو (?:داود|عيسي|عبد الرحمن|عبد الله|عوانه|محمد|حاتم|عمر|جعفر|القاسم|يعلي|عبيد|بكر)"
    r"|الشافعي|احمد|الشيخ|البخاري|مسلم|البيهقي)"
    r"|(?:و)?هذا (?:حديث|لفظ|اسناد|اصح|غريب|منكر)|هذا هو (?:الصحيح|المحفوظ|الصواب)"
    r"|وهذا الحديث|غريب (?:من|عن)|والمحفوظ|(?:و)?في روايه|(?:و)?(?:رواه|اخرجه|اخرجاه|تابعه)"
    r"|وروي|وقد روي|قد (?:خرجا|اخرجا|احتج)|(?:و)?لم يخرجاه"
    r"|(?:و)?(?:لم|لا) (?:يرو|يروه|يروي)|(?:و)?(?:تفرد|انفرد)"
    r"|(?:و)?(?:لا|لم) (?:يذكر|يذكرا|يذكران|يذكروا|يقل|يقولا)|ليس فيه"
    r"|قلت(?: [0-9]+)? (?:و)?(?:اسناد|رواه|هذا|له|مدار|اخرجه|في))"
    + END
    + r"|(?:و)?اللفظ ل|(?:و)?لفظ )"
)

# Says whose words a shared matn is: "واللفظ له", "واللفظ لقتيبه", "هذا حديث يحيي", "لفظ القهستاني".
LAFZ_HIS = re.compile(r"(?:^| )(?:و)?اللفظ له" + END)
LAFZ_NAMED = re.compile(
    r"(?:^| )(?:(?:و)?اللفظ ل|(?:و)?هذا (?:لفظ )?(?:حديث )?|(?:و)?لفظ (?:حديث )?)(?=[^ ])"
)
# Gives one chain's differing words: "وفي رواية عمرو", "وقال محمد بن العلاء في حديثه", "قال هاشم".
DIFFERENCE = re.compile(r"(?:^| )(?:و)?(?:في (?:روايه|حديث)|قال|زاد) (?=[^ ])")
DIFFERENCE_TAIL = re.compile(r"(?:في حديثه|فيه)" + END)

# Transmission words: what an isnad is made of besides names.
BACKOFF = words(
    "حدثنا حدثني حدثناه حدثنيه اخبرنا اخبرني اخبرناه انبانا انبا ثنا قثنا "
    "نا انا سمعت عن ح قال قالا قالوا كما قد ثم و زاد"
)
GLUE = BACKOFF | words(
    "جميعا كلاهما كلهم جميعهم يعني له لهما اللفظ واللفظ لفظ زاد في قالت "
    "سمع يحدث يحدثه حدثه اخبره اخبرته اخبر انه انها ان يقول سمعه يرويه يرفعه رفعه "
    "ابيه ابيها جده جدها جدي عمه عمي امه امي اخيه اخي خاله خالي مولاه مولاته ابن بن بنت"
)
# A gap between two mentions holding a matn or a formula; chains do not jump across it.
WALL = re.compile(
    rf"(?:^| )(?:{PROPHET}|(?:ب|و)?(?:مثله|مثل|نحوه|نحو|معناه|بمعني|اسناده|اسناد|الاسناد))" + END
)
MAX_LOOSE_WORDS = 6
# Words of a comment on transmission, which a chain cited in the collector's comment may carry
# instead of a matn: "وإنما هذا إسناد حديث ابن المحبق".
ABOUT_ISNADS = re.compile(
    r"(?:^| )(?:و)?(?:اسناد|الاسناد|اسناده|رواه|وهم|خطا|مرسل|منكر|ضعيف|صحيح|يصح|محفوظ)" + END
)
