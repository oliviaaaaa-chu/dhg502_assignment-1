from qhchina import load_stopwords
from qhchina.analytics.collocations import find_collocates


def load_sentences(path="sentences.txt"):
    with open(path, encoding="utf-8") as f:
        return [line.split() for line in f if line.strip()]


def run(method, horizon=None, filename=""):
    sentences = load_sentences()
    filters = {
        "stopwords": load_stopwords("zh_cl_sim"),
        "min_word_length": 2,
        "min_obs_local": 3,
    }
    df = find_collocates(
        sentences,
        "东林",
        method=method,
        horizon=horizon,
        measures=["log_likelihood", "logDice"],
        filters=filters,
        correction="fdr_bh",
    )
    df = df[df["adjusted_p_value"] < 0.05]
    df = df.sort_values("log_dice", ascending=False)
    df.to_csv(f"output/{filename}", index=False)
    print(f"\n=== {method}" + (f", horizon={horizon}" if horizon is not None else "") + f" -> output/{filename} ===")
    print(df.head(20).to_string(index=False))


def main():
    import os

    os.makedirs("output", exist_ok=True)
    run("window", 5, "collocates_window_h5.csv")
    run("window", 10, "collocates_window_h10.csv")
    run("sentence", None, "collocates_sentence.csv")


if __name__ == "__main__":
    main()
