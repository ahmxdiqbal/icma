#!/usr/bin/env python3
"""Count Qwen3 vs Qwen3.5 tokens on hadith-kg entries, with and without harakat.

Pure-Python emulation of the Hugging Face tokenizers pipeline declared in each
tokenizer.json: NFC normalizer -> regex Split (Isolated) -> ByteLevel -> BPE.
Usage: tokcount.py DB_PATH SAMPLE_SIZE SEED TOKENIZER_JSON [TOKENIZER_JSON ...]
"""
import json
import random
import sqlite3
import sys
import unicodedata
from collections import defaultdict

HARAKAT = frozenset(chr(c) for c in range(0x064B, 0x0653)) | {"ٰ"}
CONTRACTIONS = ("'s", "'t", "'re", "'ve", "'m", "'ll", "'d")


def cat0(c: str) -> str:
    return unicodedata.category(c)[0]


class PreTokenizer:
    """Scanner equivalent to the Qwen regex; marks_in_words selects Qwen3.5 form."""

    def __init__(self, marks_in_words: bool) -> None:
        self.marks_in_words = marks_in_words

    def word_char(self, c: str) -> bool:
        k = cat0(c)
        return k == "L" or (self.marks_in_words and k == "M")

    def punct_char(self, c: str) -> bool:
        k = cat0(c)
        if c.isspace() or k in ("L", "N"):
            return False
        return not (self.marks_in_words and k == "M")

    @staticmethod
    def run(t: str, j: int, pred) -> int:
        while j < len(t) and pred(t[j]):
            j += 1
        return j

    def match_end(self, t: str, i: int) -> int:
        n, c = len(t), t[i]
        if c == "'":
            low = t[i : i + 3].lower()
            for k in CONTRACTIONS:
                if low.startswith(k):
                    return i + len(k)
        if c not in "\r\n" and cat0(c) not in ("L", "N") and i + 1 < n:
            j = self.run(t, i + 1, self.word_char)
            if j > i + 1:
                return j
        j = self.run(t, i, self.word_char)
        if j > i:
            return j
        if cat0(c) == "N":
            return i + 1
        start = i + 1 if (c == " " and i + 1 < n and self.punct_char(t[i + 1])) else i
        if self.punct_char(t[start]):
            j = self.run(t, start, self.punct_char)
            return self.run(t, j, lambda ch: ch in "\r\n")
        k = self.run(t, i, str.isspace)
        if k > i:
            newlines = [p for p in range(i, k) if t[p] in "\r\n"]
            if newlines:
                return newlines[-1] + 1
            if k == n:
                return k
            return k - 1 if k - 1 > i else k
        return i + 1

    def split(self, t: str) -> list:
        out, i = [], 0
        while i < len(t):
            j = self.match_end(t, i)
            out.append(t[i:j])
            i = j
        return out


def bytes_to_unicode() -> dict:
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1))
    bs += list(range(ord("®"), ord("ÿ") + 1))
    cs, n = bs[:], 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, map(chr, cs)))


class ByteBPE:
    def __init__(self, path: str) -> None:
        t = json.load(open(path, encoding="utf-8"))
        m = t["model"]
        self.vocab = m["vocab"]
        self.ranks = {}
        for r, mg in enumerate(m["merges"]):
            a, b = mg if isinstance(mg, list) else mg.split(" ", 1)
            self.ranks[(a, b)] = r
        self.ignore_merges = bool(m.get("ignore_merges", False))
        regex = t["pre_tokenizer"]["pretokenizers"][0]["pattern"]["Regex"]
        self.pre = PreTokenizer(marks_in_words="\\p{M}]+" in regex)
        self.b2u = bytes_to_unicode()
        self.cache = {}

    def bpe(self, word: str) -> list:
        parts = list(word)
        while len(parts) > 1:
            best, best_rank = -1, None
            for i in range(len(parts) - 1):
                r = self.ranks.get((parts[i], parts[i + 1]))
                if r is not None and (best_rank is None or r < best_rank):
                    best, best_rank = i, r
            if best < 0:
                break
            a, b = parts[best], parts[best + 1]
            merged, i = [], 0
            while i < len(parts):
                if i < len(parts) - 1 and parts[i] == a and parts[i + 1] == b:
                    merged.append(a + b)
                    i += 2
                else:
                    merged.append(parts[i])
                    i += 1
            parts = merged
        return parts

    def count_piece(self, piece: str) -> int:
        hit = self.cache.get(piece)
        if hit is not None:
            return hit
        w = "".join(self.b2u[b] for b in piece.encode("utf-8"))
        if self.ignore_merges and w in self.vocab:
            n = 1
        else:
            toks = self.bpe(w)
            assert all(x in self.vocab for x in toks), (piece, toks)
            n = len(toks)
        self.cache[piece] = n
        return n

    def count(self, text: str) -> int:
        text = unicodedata.normalize("NFC", text)
        return sum(self.count_piece(p) for p in self.pre.split(text))


def dediac(s: str) -> str:
    return "".join(c for c in s if c not in HARAKAT)


def vocal_class(letters: int, marks: int) -> str:
    ratio = marks / letters if letters else 0.0
    if ratio < 0.05:
        return "unvocalized(<0.05 marks/letter)"
    return "partial(0.05-0.5)" if ratio < 0.5 else "full(>=0.5)"


def main() -> None:
    db, size, seed, paths = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
    toks = [(p.split("models--")[1].split("/")[0], ByteBPE(p)) for p in paths]
    for name, tk in toks:
        print(f"{name}: vocab={len(tk.vocab)} marks_in_words={tk.pre.marks_in_words}"
              f" ignore_merges={tk.ignore_merges}")
        demo = "حَدَّثَنَا"
        print("   pre-tokens of", demo, "->", tk.pre.split(unicodedata.normalize("NFC", " " + demo)),
              "tokens:", tk.count(" " + demo), "| undiacritized:", tk.count(" " + dediac(demo)))
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    ids = [r[0] for r in con.execute("select id from hadiths")]
    random.Random(seed).shuffle(ids)
    agg = defaultdict(lambda: defaultdict(int))
    books = defaultdict(lambda: defaultdict(int))
    lengths = []
    per_entry = defaultdict(list)
    for hid in ids[:size]:
        bid, bname, nass = con.execute(
            "select h.book_id, b.name, h.nass from hadiths h join books b on b.id=h.book_id"
            " where h.id=?", (hid,)).fetchone()
        nass = unicodedata.normalize("NFC", nass)
        letters = sum(1 for c in nass if "ء" <= c <= "ي")
        marks = sum(1 for c in nass if c in HARAKAT)
        cls = vocal_class(letters, marks)
        plain = dediac(nass)
        row = {"entries": 1, "chars": len(nass), "chars_plain": len(plain), "letters": letters,
               "marks": marks, "words": len(nass.split())}
        for name, tk in toks:
            row[f"{name}|orig"] = tk.count(nass)
            row[f"{name}|plain"] = tk.count(plain)
        for key in ("ALL", cls):
            for k, v in row.items():
                agg[key][k] += v
        books[bname][cls] += 1
        lengths.append(len(nass))
        for name, _ in toks:
            per_entry[f"{name}|orig"].append(row[f"{name}|orig"])
            per_entry[f"{name}|plain"].append(row[f"{name}|plain"])
    print("\nper-entry token distribution (p50/p90/p99/max; share of entries over 1024/2048/4096 tokens):")
    for key, vals in per_entry.items():
        vals.sort()
        pq = lambda p: vals[min(len(vals) - 1, int(p * len(vals)))]
        over = [sum(1 for v in vals if v > lim) / len(vals) * 100 for lim in (1024, 2048, 4096)]
        print(f"   {key:40s} p50={pq(0.5)} p90={pq(0.9)} p99={pq(0.99)} max={vals[-1]}"
              f" | >1024: {over[0]:.2f}% >2048: {over[1]:.2f}% >4096: {over[2]:.3f}%")
    lengths.sort()
    q = lambda p: lengths[min(len(lengths) - 1, int(p * len(lengths)))]
    print(f"\nsample={size} seed={seed} chars/entry p50={q(0.5)} p90={q(0.9)} p99={q(0.99)} max={lengths[-1]}")
    for key, a in sorted(agg.items()):
        n = a["entries"]
        print(f"\n[{key}] entries={n} mean_chars={a['chars']/n:.0f} mean_words={a['words']/n:.1f}"
              f" marks_per_letter={a['marks']/max(1,a['letters']):.2f}")
        for name, _ in toks:
            o, p = a[f"{name}|orig"], a[f"{name}|plain"]
            print(f"   {name:34s} orig: {o/n:7.1f} tok/entry {o/a['words']:.2f} tok/word"
                  f" {a['chars']/o:.2f} chars/tok | plain: {p/n:7.1f} tok/entry {p/a['words']:.2f} tok/word"
                  f" | inflation x{o/p:.2f}")
    print("\nbooks by vocalization class (top 12 by sample count):")
    for bname, d in sorted(books.items(), key=lambda kv: -sum(kv[1].values()))[:12]:
        print("  ", bname, dict(d))


if __name__ == "__main__":
    main()
