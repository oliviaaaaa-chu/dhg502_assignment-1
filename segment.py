#!/usr/bin/env python3
"""Segment 明史.txt into jieba-tokenized, simplified-Chinese sentences.

Pipeline:
1. Load 明史.txt (traditional characters, UTF-8) and convert to simplified with opencc.
2. Write userdict.txt (one word per line) with the target words (東林 + related
   names and official titles), converted to simplified, and load it into jieba.
3. Split the text into sentences on 。！？；, tokenize with jieba, drop
   punctuation tokens, and keep only sentences with at least 5 words.
4. Save sentences to sentences.txt (words separated by a single space) and, since
   the source marks chapters (卷N headings), save sentence_index.csv mapping each
   line of sentences.txt to its 卷 number and title.
5. Print 20 random segmented sentences containing a target word for eyeballing.
"""

import csv
import random
import re
from pathlib import Path

import jieba
import opencc

jieba.setLogLevel(60)

BASE = Path(__file__).resolve().parent
SRC = BASE / "明史.txt"
SENTENCES_TXT = BASE / "sentences.txt"
SENTENCE_INDEX_CSV = BASE / "sentence_index.csv"
USERDICT_TXT = BASE / "userdict.txt"

# Target words in traditional script (as they appear in the source text);
# the script converts them to simplified for the jieba user dictionary.
TARGET_WORDS = [
    # the faction and its institution
    "東林",
    "東林黨",
    "東林黨人",
    "東林書院",
    "閹黨",
    "復社",
    # leading Donglin figures
    "顧憲成",
    "顧允成",
    "高攀龍",
    "錢一本",
    "薛敷教",
    "趙南星",
    "鄒元標",
    "葉向高",
    "楊漣",
    "左光鬥",
    "魏大中",
    "周順昌",
    "繆昌期",
    "李應昇",
    "周宗建",
    "黃尊素",
    "顧大章",
    "袁化中",
    "馮從吾",
    "孫慎行",
    "劉宗周",
    "黃道周",
    "錢謙益",
    # protest figures of the 奪情 controversy that seeded the faction
    "吳中行",
    "趙用賢",
    # rival (eunuch / court) figures
    "魏忠賢",
    "客氏",
    "崔呈秀",
    "阮大鋮",
    "馬士英",
    "溫體仁",
    "周延儒",
    "顧秉謙",
    # related official titles and institutions
    "大學士",
    "內閣",
    "首輔",
    "次輔",
    "給事中",
    "都給事中",
    "御史",
    "都御史",
    "左都御史",
    "右都御史",
    "副都御史",
    "左副都御史",
    "右副都御史",
    "僉都御史",
    "都察院",
    "巡按",
    "巡撫",
    "總督",
    "尚書",
    "吏部尚書",
    "戶部尚書",
    "禮部尚書",
    "兵部尚書",
    "刑部尚書",
    "工部尚書",
    "侍郎",
    "左侍郎",
    "右侍郎",
    "郎中",
    "員外郎",
    "祭酒",
    "司業",
    "國子監",
    "翰林院",
    "翰林學士",
    "國子祭酒",
    "詹事",
    "科道",
    "京察",
    "廷杖",
    "詔獄",
    "司禮監",
    "東廠",
    "錦衣衛",
]

# The 明史 standard structure: 本紀 24 juan, 志 75, 表 13, 列傳 220 (= 332).
JUAN_RANGES = (
    (1, 24, "本纪"),
    (25, 99, "志"),
    (100, 112, "表"),
    (113, 332, "列传"),
)

JUAN_HEADING_RE = re.compile(r"^卷([〇零一二三四五六七八九十百]+)$")
TITLE_RE = re.compile(r"^【?\s*((?:本紀|本纪|志|表|列傳|列传)第[〇零一二三四五六七八九十百]+.*)】?\s*$")
TOC_LIST_RE = re.compile(r"^○.*〈")
FOOTNOTE_RE = re.compile(r"[［\[]\s*[0-9０-９]+\s*[］\]]")
BOILERPLATE_RE = re.compile(r"公有领域|公有領域")
MARKDOWN_RULE_RE = re.compile(r"^[-=]+$")
SENTENCE_SPLIT_RE = re.compile(r"[。！？；]")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
JUAN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
               "六": 6, "七": 7, "八": 8, "九": 9}


def cn_to_int(s):
    """Convert a Chinese-numeral string like 一百〇一 to an integer."""
    total, cur = 0, 0
    for ch in s:
        if ch in JUAN_DIGITS:
            cur = JUAN_DIGITS[ch]
        elif ch == "十":
            total += (cur or 1) * 10
            cur = 0
        elif ch == "百":
            total += (cur or 1) * 100
            cur = 0
    return total + cur


def int_to_cn(n):
    """Convert an integer (1-999) to a Chinese-numeral string, e.g. 110 -> 一百一十."""
    digits = "零一二三四五六七八九"
    if n < 10:
        return digits[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        tens_part = "十" if tens == 1 else digits[tens] + "十"
        return tens_part + (digits[ones] if ones else "")
    hundreds, rem = divmod(n, 100)
    head = digits[hundreds] + "百"
    if rem == 0:
        return head
    if rem < 10:
        return head + "零" + digits[rem]
    if rem < 20:
        return head + "一" + int_to_cn(rem)
    return head + int_to_cn(rem)


def juan_label(n):
    """Standard structural label for a 明史 卷 number, e.g. 138 -> 列传第二十六."""
    for lo, hi, kind in JUAN_RANGES:
        if lo <= n <= hi:
            return f"{kind}第{int_to_cn(n - lo + 1)}"
    return f"卷第{int_to_cn(n)}"


def write_userdict(converter):
    """Write userdict.txt (one word per line) and load it into jieba."""
    seen = set()
    lines = []
    for word in TARGET_WORDS:
        simplified = converter.convert(word)
        if simplified not in seen:
            seen.add(simplified)
            lines.append(simplified)
    USERDICT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    jieba.load_userdict(str(USERDICT_TXT))
    return seen


def tokenize(sentence):
    """Split a sentence into words with jieba, dropping punctuation tokens."""
    return [w for w in jieba.cut(sentence) if CJK_RE.search(w)]


def main():
    converter = opencc.OpenCC("t2s.json")
    targets = write_userdict(converter)

    lines = converter.convert(SRC.read_text(encoding="utf-8")).splitlines()

    # First pass: locate each 卷 heading and its title (if the source provides one).
    chapters = []  # (start_line, juan_number, title_or_None)
    for i, line in enumerate(lines):
        m = JUAN_HEADING_RE.match(line.strip())
        if m:
            chapters.append((i, cn_to_int(m.group(1)), None))

    # Attach explicit titles: look a couple of non-empty lines ahead of the heading
    # for a "本紀/志/表/列傳第N" line (sometimes wrapped in 【】).
    for idx, (start, juan, _) in enumerate(chapters):
        stop = chapters[idx + 1][0] if idx + 1 < len(chapters) else len(lines)
        j = start + 1
        found = 0
        while j < stop and found < 2:
            stripped = lines[j].strip()
            if stripped:
                m = TITLE_RE.match(stripped)
                if m:
                    title = converter.convert(m.group(1).strip("【】"))
                    if len(title) > 50:
                        title = title[:50] + "…"
                    chapters[idx] = (start, juan, title)
                    lines[j] = ""  # consume the title line
                    found += 1
            j += 1

    sentences = []   # list of (line_no, juan, title, segmented_string)
    chapters_idx = 0
    current_juan = None
    current_title = None
    first_snippet = None

    heading_lines = {start for start, _, _ in chapters}
    for i, line in enumerate(lines):
        while chapters_idx < len(chapters) and chapters[chapters_idx][0] == i:
            current_juan = chapters[chapters_idx][1]
            current_title = chapters[chapters_idx][2]
            first_snippet = None
            chapters_idx += 1

        stripped = line.strip()
        if (not stripped or i in heading_lines or TOC_LIST_RE.match(stripped)
                or MARKDOWN_RULE_RE.match(stripped)
                or BOILERPLATE_RE.search(stripped) or current_juan is None):
            continue

        clean = FOOTNOTE_RE.sub("", stripped)
        for sentence in SENTENCE_SPLIT_RE.split(clean):
            sentence = sentence.strip()
            if not sentence:
                continue
            if first_snippet is None:
                lead = re.sub(r"^[^\u3400-\u9fff]+", "", sentence)
                first_snippet = lead[:12]

            words = tokenize(sentence)
            if len(words) < 5:
                continue
            if current_title is None:
                current_title = f"{juan_label(current_juan)}：{first_snippet}"
            sentences.append((len(sentences) + 1, current_juan, current_title,
                              " ".join(words), sentence))

    with SENTENCES_TXT.open("w", encoding="utf-8") as f:
        for _, _, _, seg, _ in sentences:
            f.write(seg + "\n")

    with SENTENCE_INDEX_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["line", "juan", "title", "orig"])
        for line_no, juan, title, _, orig in sentences:
            writer.writerow([line_no, juan, title, orig])

    print(f"chapters (卷): {len(chapters)}")
    print(f"sentences kept: {len(sentences)}  ->  {SENTENCES_TXT.name}, "
          f"index in {SENTENCE_INDEX_CSV.name}")

    hits = [s for s in sentences if any(t in s[3] for t in targets)]
    sample = random.sample(hits, min(20, len(hits)))
    print(f"\n{len(sample)} random segmented sentences containing a target word:\n")
    for line_no, juan, title, seg, _ in sample:
        print(f"[line {line_no}] 卷{int_to_cn(juan)} ({title})")
        print(f"    {seg}\n")


if __name__ == "__main__":
    main()
