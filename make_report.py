import csv
from pathlib import Path

OUTPUT_DIR = Path("output")
REPORT = OUTPUT_DIR / "results.html"

LABELS = {
    "collocates_window_h5.csv": "Window (horizon = 5)",
    "collocates_window_h10.csv": "Window (horizon = 10)",
    "collocates_sentence.csv": "Sentence",
}


def load_runs():
    runs = []
    for path in sorted(OUTPUT_DIR.glob("*.csv")):
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            for key, value in row.items():
                try:
                    row[key] = float(value)
                except (TypeError, ValueError):
                    pass
        runs.append({"name": path.name, "label": LABELS.get(path.name, path.name), "rows": rows})
    return runs


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>东林 collocates</title>
<style>
  body { font-family: "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;
         margin: 2rem; background: #fafafa; color: #222; }
  h1 { font-size: 1.4rem; }
  .controls { margin-bottom: 1rem; }
  select { font-size: 1rem; padding: .3rem .5rem; }
  table { border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.15); }
  th, td { border: 1px solid #ddd; padding: .35rem .7rem; text-align: right; white-space: nowrap; }
  td:nth-child(2) { text-align: left; }
  th { background: #2c3e50; color: #fff; cursor: pointer; user-select: none; }
  th:hover { background: #34495e; }
  th .arrow { margin-left: .3em; }
  th.sorted-asc, th.sorted-desc { background: #1a6f8a; }
  tr:nth-child(even) { background: #f2f6f8; }
</style>
</head>
<body>
<h1>Collocates of 东林</h1>
<div class="controls">
  <label for="run">Run:</label>
  <select id="run"></select>
  <span id="count" style="margin-left:1rem; color:#666;"></span>
</div>
<table id="tbl"><thead></thead><tbody></tbody></table>

<script>
const RUNS = __DATA__;
let current = RUNS[0];
let sortKey = "log_dice";
let sortDir = -1;

const select = document.getElementById("run");
const thead = document.querySelector("#tbl thead");
const tbody = document.querySelector("#tbl tbody");
const countEl = document.getElementById("count");

RUNS.forEach((run, i) => {
  const opt = document.createElement("option");
  opt.value = i;
  opt.textContent = run.label;
  select.appendChild(opt);
});

select.addEventListener("change", () => {
  current = RUNS[select.value];
  sortKey = "log_dice";
  sortDir = -1;
  render();
});

function isNumeric(key) {
  return current.rows.every(r => typeof r[key] === "number");
}

function fmt(v) {
  if (typeof v === "number") {
    if (v !== 0 && (Math.abs(v) < 1e-4 || Math.abs(v) >= 1e6)) return v.toExponential(2);
    return String(Math.round(v * 1e6) / 1e6);
  }
  return v;
}

function render() {
  const cols = Object.keys(current.rows[0]);
  thead.innerHTML = "<tr>" + cols.map(c => {
    let arrow = "";
    let cls = "";
    if (c === sortKey) {
      cls = sortDir === 1 ? "sorted-asc" : "sorted-desc";
      arrow = sortDir === 1 ? "▲" : "▼";
    }
    return `<th class="${cls}" data-col="${c}">${c}<span class="arrow">${arrow}</span></th>`;
  }).join("") + "</tr>";

  const rows = [...current.rows].sort((a, b) => {
    const va = a[sortKey], vb = b[sortKey];
    let cmp;
    if (typeof va === "number" && typeof vb === "number") cmp = va - vb;
    else cmp = String(va).localeCompare(String(vb), "zh");
    return cmp * sortDir;
  });

  tbody.innerHTML = rows.map(r =>
    "<tr>" + cols.map(c => `<td>${fmt(r[c])}</td>`).join("") + "</tr>"
  ).join("");

  countEl.textContent = `${rows.length} collocates`;

  thead.querySelectorAll("th").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (col === sortKey) sortDir = -sortDir;
      else { sortKey = col; sortDir = isNumeric(col) ? -1 : 1; }
      render();
    });
  });
}

render();
</script>
</body>
</html>
"""


def main():
    runs = load_runs()
    if not runs:
        raise SystemExit("No CSV files found in output/")
    import json

    REPORT.write_text(HTML.replace("__DATA__", json.dumps(runs, ensure_ascii=False)), encoding="utf-8")
    print(f"Wrote {REPORT} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
