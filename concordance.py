import csv
import html
from pathlib import Path

import opencc
from qhchina.analytics.collocations import kwic

TARGET = "东林"
S2T = opencc.OpenCC("s2t.json")
OUTPUT_DIR = Path("output")
OUT_HTML = OUTPUT_DIR / "kwic.html"
MAX_LINES = 10
CJK_RE = None  # set lazily; kept simple via str checks in has_cjk


def load_collocates():
    """Union of collocates from the CSVs behind results.html, best log_dice first."""
    best = {}
    for path in sorted(OUTPUT_DIR.glob("collocates_*.csv")):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                c, dice = row["collocate"], float(row["log_dice"])
                if c not in best or dice > best[c]:
                    best[c] = dice
    return sorted(best, key=best.get, reverse=True)


def load_index():
    path = Path("sentence_index.csv")
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return {int(r["line"]): (r["juan"], r["title"], r["orig"]) for r in csv.DictReader(f)}


def has_cjk(s):
    return any("\u3400" <= ch <= "\u9fff" for ch in s)


def align(tokens, orig):
    """Map each token to its (start, end) char span in the original sentence.

    Tokens are consecutive slices of the original sentence with pure
    non-CJK tokens dropped, so a sequential search recovers the spans.
    Returns None if the alignment fails (then we fall back to plain tokens).
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


def render_side(orig, tokens, spans, lo, hi, lo_char, hi_char, collocate):
    """HTML for one context side: chars in [lo_char, hi_char) with the
    tokens [lo, hi) wrapped when they equal the collocate; chars between
    tokens (the dropped punctuation) are shown as-is."""
    out, cur = [], lo_char
    for i in range(lo, hi):
        a, b = spans[i]
        if cur < a:
            out.append(html.escape(orig[cur:a]))
        text = html.escape(orig[a:b])
        if tokens[i] == collocate:
            out.append(f'<span class="coll">{text}</span>')
        else:
            out.append(text)
        cur = b
    if cur < hi_char:
        out.append(html.escape(orig[cur:hi_char]))
    return "".join(out)


def build_row(i, line, collocate, all_tokens, index, span_cache):
    pos = line["position"]
    left, right = line["left_tokens"], line["right_tokens"]
    juan, title, orig = index.get(line["doc_index"] + 1, ("", "", ""))
    tokens = all_tokens[line["doc_index"]]
    if not orig:
        left_txt = S2T.convert("".join(left))
        right_txt = S2T.convert("".join(right))
        node_txt = S2T.convert(line["node"])
        return f"<tr><td>{i}</td><td>{S2T.convert(juan)}</td><td>{S2T.convert(title)}</td><td class='ctx'>{left_txt}</td><td class='node'>{node_txt}</td><td class='ctx'>{right_txt}</td></tr>"

    if line["doc_index"] not in span_cache:
        span_cache[line["doc_index"]] = align(tokens, orig)
    spans = span_cache[line["doc_index"]]
    if spans is None or len(spans) != len(tokens):
        left_txt = S2T.convert("".join(left))
        right_txt = S2T.convert("".join(right))
        node_txt = S2T.convert(line["node"])
        return f"<tr><td>{i}</td><td>{S2T.convert(juan)}</td><td>{S2T.convert(title)}</td><td class='ctx'>{left_txt}</td><td class='node'>{node_txt}</td><td class='ctx'>{right_txt}</td></tr>"

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

    left_txt = render_side(orig, tokens, spans, first_l, pos, lo_char, spans[pos][0], collocate)
    right_txt = render_side(orig, tokens, spans, pos + 1, last_r + 1, spans[pos][1], hi_char, collocate)
    left_txt = S2T.convert(left_txt)
    right_txt = S2T.convert(right_txt)
    node_txt = S2T.convert(line["node"])
    juan_t, title_t = S2T.convert(juan), S2T.convert(title)
    return (f"<tr><td>{i}</td><td>{juan_t}</td><td>{title_t}</td>"
            f"<td class='ctx'>{left_txt}</td><td class='node'>{node_txt}</td>"
            f"<td class='ctx'>{right_txt}</td></tr>")


def build_runs(lines, collocate, tokens, index, span_cache):
    hits = [
        l for l in lines
        if collocate in l["left_tokens"] or collocate in l["right_tokens"]
    ][:MAX_LINES]
    rows = [build_row(i, l, collocate, tokens, index, span_cache) for i, l in enumerate(hits, 1)]
    return hits, rows


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
  table { border-collapse: collapse; background: #fff; width: 100%; }
  th, td { border: 1px solid #ddd; padding: .3rem .6rem; vertical-align: top; }
  th { background: #2c3e50; color: #fff; text-align: left; }
  td.ctx { width: 42%; }
  th.node, td.node { background: #ffd54f; font-weight: bold; text-align: center; }
  .coll { background: #90caf9; font-weight: bold; }
  .meta { color: #666; font-size: .9rem; }
  .missing { color: #b00; }
</style>
</head>
<body>
<h1>KWIC：東林與關鍵詞共現段落</h1>
<p class="meta">視窗 ±10 詞，每個搭配詞最多 {max_lines} passages per collocate. Highlighted: <span class="node">東林</span>（節點）及<span class="coll">搭配詞</span>。</p>
{body}
</body>
</html>
"""


def main():
    sentences = [l.split() for l in open("sentences.txt", encoding="utf-8")]
    index = load_index()
    collocates = load_collocates()
    lines = kwic(sentences, target=TARGET, horizon=10, sort_by="position", return_type="list")

    span_cache = {}
    parts = []
    n_found = 0
    for collocate in collocates:
        hits, rows = build_runs(lines, collocate, sentences, index, span_cache)
        if rows:
            n_found += 1
        parts.append(
            f"<h2>東林 × {S2T.convert(collocate)} <span class='meta'>({len(hits)} passage{'' if len(hits) == 1 else 's'})</span></h2>"
        )
        if rows:
            parts.append(
                "<table><tr><th>id</th><th>卷</th><th>題名</th><th>左語境</th><th class='node'>東林</th><th>右語境</th></tr>"
                + "\n".join(rows) + "</table>"
            )
        else:
            parts.append("<p class='missing'>No co-occurrence within horizon 10.</p>")

    OUT_HTML.write_text(
        PAGE.replace("{body}", "\n".join(parts)).replace("{max_lines}", str(MAX_LINES)), encoding="utf-8"
    )
    print(f"Wrote {OUT_HTML}: {len(collocates)} collocates, {n_found} with co-occurrences")


if __name__ == "__main__":
    main()
