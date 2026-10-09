import html
import re
from pathlib import Path

import opencc
from qhchina.analytics.collocations import kwic

# Target word and collocates as given (mixed simplified/traditional input).
TARGET = "東林"
COLLOCATES = [
    "顾宪成", "魏忠贤", "李三才", "黨人", "復社",
    "玉立", "削籍", "其黨", "削奪", "高攀龍",
]

MAX_LINES = 10
OUTPUT_DIR = Path("output")
OUT_HTML = OUTPUT_DIR / "kwic.html"

S2T = opencc.OpenCC("s2t.json")

# The corpus is simplified Chinese; match in simplified, display in traditional.
T2S = opencc.OpenCC("t2s.json")
METHODS = [
    ("window", 5),
    ("window", 10),
    ("sentence", None),
]


def load_index():
    """Map sentence line number (1-based) -> (juan, title, orig)."""
    path = Path("sentence_index.csv")
    if not path.exists():
        return {}
    import csv
    with open(path, encoding="utf-8-sig") as f:
        return {
            int(r["line"]): (r["juan"], r["title"], r["orig"])
            for r in csv.DictReader(f)
        }


def esc(s):
    return html.escape(s)


def highlight(text, word):
    """Wrap every occurrence of word in text with a <span class='coll'>."""
    if not word:
        return text
    return re.sub(
        re.escape(word),
        lambda m: f"<span class='coll'>{m.group(0)}</span>",
        text,
    )


def align(tokens, orig):
    """Map each token to its (start, end) char span in the original sentence.

    Tokens are consecutive slices of the original sentence, so a sequential
    search recovers the spans. Returns None if alignment fails.
    """
    spans = []
    pos = 0
    for tok in tokens:
        idx = orig.find(tok, pos)
        if idx < 0:
            return None
        spans.append((idx, idx + len(tok)))
        pos = idx + len(tok)
    return spans


def has_cjk(s):
    return any("\u3400" <= ch <= "\u9fff" for ch in s)


def render_side(orig, tokens, spans, lo, hi, lo_char, hi_char):
    """HTML for one context side: original chars in [lo_char, hi_char),
    including the dropped punctuation between tokens."""
    out, cur = [], lo_char
    for i in range(lo, hi):
        a, b = spans[i]
        if cur < a:
            out.append(orig[cur:a])
        out.append(orig[a:b])
        cur = b
    if cur < hi_char:
        out.append(orig[cur:hi_char])
    return "".join(out)


def build_row(l, index, span_cache):
    """Recover the original (punctuated) context around the node."""
    pos = l["position"]
    left, right = l["left_tokens"], l["right_tokens"]
    juan, title, orig = index.get(l["doc_index"] + 1, ("", "", ""))
    if not orig:
        return juan, title, "".join(left), "".join(right)
    tokens = SENTENCES[l["doc_index"]]
    if l["doc_index"] not in span_cache:
        span_cache[l["doc_index"]] = align(tokens, orig)
    spans = span_cache[l["doc_index"]]
    if spans is None or len(spans) != len(tokens):
        return juan, title, "".join(left), "".join(right)

    n = len(tokens)
    first_l = pos - len(left)
    lo_char = spans[first_l][0] if left else spans[pos][0]
    if first_l > 0:
        gap = orig[spans[first_l - 1][1]:spans[first_l][0]]
        if gap and not has_cjk(gap):
            lo_char = spans[first_l - 1][1]
    last_r = pos + len(right)
    hi_char = spans[last_r][1] if right else spans[pos][1]
    nxt = last_r + 1
    if nxt < n:
        gap = orig[spans[last_r][1]:spans[nxt][0]]
        if gap and not has_cjk(gap):
            hi_char = spans[nxt][0]
    else:
        tail = orig[spans[last_r][1]:]
        if tail and not has_cjk(tail):
            hi_char = len(orig)

    left_txt = render_side(orig, tokens, spans, first_l, pos, lo_char, spans[pos][0])
    right_txt = render_side(orig, tokens, spans, pos + 1, last_r + 1, spans[pos][1], hi_char)
    return juan, title, left_txt, right_txt


def build_section(lines, index, horizon):
    """One HTML table per collocate with up to MAX_LINES co-occurrence rows."""
    out = []
    span_cache = {}
    for coll in COLLOCATES:
        coll_s = T2S.convert(coll)
        coll_t = S2T.convert(coll)
        hits = [
            l for l in lines
            if coll_s in "".join(l["left_tokens"]) + l["node"] + "".join(l["right_tokens"])
        ][:MAX_LINES]
        out.append(
            f"<h2>東林 × {esc(coll_t)} <span class='meta'>({len(hits)} passage"
            f"{'' if len(hits) == 1 else 's'})</span></h2>"
        )
        if not hits:
            out.append("<p class='missing'>No co-occurrence found.</p>")
            continue
        rows = []
        for i, l in enumerate(hits, 1):
            juan, title, left, right = build_row(l, index, span_cache)
            node = S2T.convert(l["node"])
            rows.append(
            f"<tr><td class='id'>{i}</td><td class='juan'>{esc(S2T.convert(juan))}</td>"
            f"<td class='title'>{esc(S2T.convert(title))}</td>"
            f"<td class='ctx'>{highlight(S2T.convert(left), coll_t)}</td>"
            f"<td class='node'>{esc(node)}</td>"
            f"<td class='ctx'>{highlight(S2T.convert(right), coll_t)}</td></tr>"
            )
        out.append(
            "<table><tr><th class='id'>#</th><th class='juan'>卷</th><th class='title'>題名</th>"
            "<th>左語境</th><th class='node'>東林</th><th>右語境</th></tr>"
            + "\n".join(rows) + "</table>"
        )
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>東林 KWIC</title>
<style>
  body { font-family: "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;
         margin: 2rem; background: #fafafa; color: #222; }
  h1 { font-size: 1.4rem; }
  h2 { font-size: 1.1rem; margin: 1.6rem 0 .4rem; border-bottom: 2px solid #2c3e50; padding-bottom: .2rem; }
  table { border-collapse: collapse; background: #fff; width: 100%; table-layout: fixed; margin-bottom: 1.5rem; }
  th, td { border: 1px solid #ddd; padding: .3rem .6rem; vertical-align: top; }
  th { background: #2c3e50; color: #fff; text-align: left; }
  td.ctx { width: 40%; word-break: break-all; }
  th.id, td.id { width: 2.5rem; text-align: center; }
  th.juan, td.juan { width: 3.5rem; text-align: center; }
  th.title, td.title { width: 20%; }
  th.node, td.node { background: #ffd54f; font-weight: bold; text-align: center;
                     width: 6rem; white-space: nowrap; font-size: 1.05rem; letter-spacing: .1em; }
  .coll { background: #90caf9; font-weight: bold; }
  .meta { color: #666; font-size: .9rem; font-weight: normal; }
  .missing { color: #b00; }
</style>
</head>
<body>
<h1>KWIC：東林與關鍵詞共現段落</h1>
<p class="meta">Target: <span class="node">東林</span>; highlighted: <span class="coll">搭配詞</span>.
Up to {max_lines} passages per collocate. Sections: window horizon=5, window horizon=10, sentence.</p>
{body}
</body>
</html>
"""


def main():
    global SENTENCES
    sentences = [l.split() for l in open("sentences.txt", encoding="utf-8")]
    SENTENCES = sentences
    index = load_index()
    max_len = max(len(s) for s in sentences)

    sections = []
    for method, horizon in METHODS:
        h = max_len if horizon is None else horizon
        label = (
            f'method="{method}", horizon={horizon}'
            if horizon is not None
            else 'method="sentence" (whole sentence)'
        )
        lines = kwic(
            sentences,
            target=T2S.convert(TARGET),
            horizon=h,
            sort_by="position",
            return_type="list",
            max_sentence_length=None,
        )
        sections.append(
            f"<h1>Method: {label}</h1>"
            + build_section(lines, index, horizon)
        )

    OUT_HTML.parent.mkdir(exist_ok=True)
    OUT_HTML.write_text(
        PAGE.replace("{body}", "\n".join(sections)).replace("{max_lines}", str(MAX_LINES)),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
