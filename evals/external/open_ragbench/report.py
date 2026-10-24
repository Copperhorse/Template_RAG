import json, sys, random

sp = sys.argv[1]


def metrics(rows, key, thr=None):
    n = len(rows)
    out = {}

    def rel(r):
        return [c >= thr for c in r["cov"]] if thr else r["doc"]

    for k in (1, 3, 5, 10):
        out[f"R@{k}"] = 100 * sum(any(rel(r)[:k]) for r in rows) / n
    out["MRR@10"] = 100 * sum(next((1 / (i + 1) for i, x in enumerate(rel(r)) if x), 0) for r in rows) / n
    return out


def ci(rows, key, thr=None, B=1000):
    rnd = random.Random(0)
    vals = []
    for _ in range(B):
        s = [rows[rnd.randrange(len(rows))] for _ in rows]
        vals.append(metrics(s, key, thr)["R@5"])
    vals.sort()
    return vals[25], vals[974]


print("| variant | level | R@1 | R@3 | R@5 | R@10 | MRR@10 |")
print("|---|---|---:|---:|---:|---:|---:|")
for v in ("full", "no_routing", "rrf", "bm25"):
    rows = json.load(open(f"{sp}/orb/res_{v}.json"))
    for lvl, thr in (("document", None), ("section>=60%", 0.6), ("section>=80%", 0.8)):
        m = metrics(rows, None, thr)
        lo, hi = ci(rows, None, thr)
        print(
            f"| {v} (n={len(rows)}) | {lvl} | "
            + " | ".join(f"{m[k]:.1f}" for k in ("R@1", "R@3", "R@5", "R@10", "MRR@10"))
            + f" | R@5 95% CI {lo:.1f}-{hi:.1f}"
        )
rows = json.load(open(f"{sp}/orb/res_full.json"))
print("\nfull, section>=60%, by source and type")
for key in ("source", "type"):
    for g in sorted({r[key] for r in rows}):
        sub = [r for r in rows if r[key] == g]
        m = metrics(sub, key, 0.6)
        d = metrics(sub, key)
        print(f"{key}={g} n={len(sub)}: doc R@5 {d['R@5']:.1f} | section R@5 {m['R@5']:.1f} MRR {m['MRR@10']:.1f}")
# foreign-document share in top 5
for v in ("full", "no_routing"):
    rows = json.load(open(f"{sp}/orb/res_{v}.json"))
    print(
        v,
        "share of top-5 chunks from another paper:",
        f"{100 * sum(1 - sum(r['doc'][:5]) / 5 for r in rows) / len(rows):.1f}%",
    )
