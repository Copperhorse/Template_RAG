import json, sys, time, urllib.request, pathlib
meta, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
s = json.load(open(meta / "slice.json")); urls = json.load(open(meta / "pdf_urls.json"))
for d in s["positive"]:
    t = out / "corpus" / f"{d}.json"
    if not t.exists():
        urllib.request.urlretrieve(f"https://huggingface.co/datasets/vectara/open_ragbench/resolve/main/pdf/arxiv/corpus/{d}.json", t)
for i, d in enumerate(s["positive"] + s["negative"]):
    t = out / "pdfs" / f"{d}.pdf"
    if t.exists() and t.stat().st_size > 10000: continue
    req = urllib.request.Request(urls[d], headers={"User-Agent": "rag-template-eval/0.1 (personal research)"})
    try:
        t.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    except Exception as e:
        print("FAILED", d, e, flush=True)
    time.sleep(3)
    if i % 20 == 0: print(i, flush=True)
print("done")
