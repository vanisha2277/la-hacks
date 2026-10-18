"""Code checks on AI output: citations must come from tool results; linker evidence must be verbatim."""
import re

from agents.linker import verbatim  # noqa: F401  (evidence check lives with the linker)

CITE_RE = re.compile(r"\[([^\[\]\n]+?)\](?!\()")
NON_PLANT = {"general", "inference"}


def check_citations(text, allowed):
    cited = []
    for group in CITE_RE.findall(text):
        cited += [c.strip() for c in group.split(",") if c.strip()]
    cited = list(dict.fromkeys(cited))
    non_plant = lambda c: re.split(r"[\s:—–-]", c, maxsplit=1)[0].lower() in NON_PLANT  # "[general — ...]" too
    unknown = [c for c in cited if c not in allowed and not non_plant(c)]
    return {"ok": not unknown, "cited": cited, "unknown": unknown,
            "plant_citations": [c for c in cited if not non_plant(c)]}


if __name__ == "__main__":
    r = check_citations("V-200 is a drum [drawing:PID-102][slack-0101]. Likely foam [inference]. See [x](http://a)", {"drawing:PID-102", "slack-0101"})
    assert r["ok"] and r["cited"] == ["drawing:PID-102", "slack-0101", "inference"], r
    r = check_citations("Made up [slack-9999], ok [general, drawing:PID-101]", {"drawing:PID-101"})
    assert r["unknown"] == ["slack-9999"], r
    assert check_citations("x [general — a heat exchanger moves heat] [inference: likely]", set())["ok"]
    print("checks ok")
