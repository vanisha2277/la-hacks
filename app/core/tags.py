"""Tag decoding (KKS primary, ISA for legacy tags) and loop grouping. Plain code, no AI."""
import re

KKS_RE = re.compile(r"\b(\d{2})([A-Z]{3})(\d{2})([A-Z]{2})(\d{3})([A-Z]?)\b")
ISA_RE = re.compile(r"\b([A-Z]{1,4})-(\d{2,4})([A-Z]?)\b")

# KKS function code: first letter = family; second letter = variable for C/D/F
KKS_FAMILY = {"A": "mechanical equipment", "B": "mechanical equipment", "C": "measuring circuit",
              "D": "closed-loop control", "E": "signal conditioning / control unit", "F": "indirect measuring",
              "G": "electrical / I&C installation", "H": "subassembly"}
KKS_VARIABLE = {"D": "density", "E": "electrical", "F": "flow", "G": "position", "H": "hand", "K": "time",
                "L": "level", "M": "moisture", "P": "pressure", "Q": "quality", "S": "speed", "T": "temperature",
                "U": "combined", "V": "viscosity", "W": "weight", "X": "neutron flux", "Y": "vibration"}
KKS_MECHANICAL = {"AA": "valve / damper", "AC": "heat exchanger", "AE": "turning, driving or lifting gear",
                  "AF": "conveyor / feeder", "AG": "generator", "AH": "heating, cooling or AC unit",
                  "AJ": "size-reduction equipment", "AM": "mixer / agitator", "AN": "compressor / fan", "AP": "pump",
                  "AS": "expansion joint", "AT": "cleaning, drying, filtering or separating equipment (column)",
                  "AU": "brake, gearbox or coupling", "AV": "combustion equipment", "AW": "stationary tooling",
                  "AX": "test / monitoring equipment", "BB": "storage tank / vessel", "BF": "foundation",
                  "BN": "jet pump, ejector or injector", "BP": "orifice / flow restrictor",
                  "BQ": "hanger, support or rack", "BR": "piping, duct or chute", "BS": "silencer", "BU": "insulation",
                  "GA": "junction box / cable", "GB": "cable or busbar penetration", "GH": "cubicle or box"}

# ISA-5.1, for legacy tags (LV-202, P-102A) that people still use
ISA_EQUIPMENT = {"P": "pump", "V": "vessel", "E": "exchanger", "T": "tank", "C": "column/compressor", "K": "compressor"}
ISA_VARIABLE = {"F": "flow", "L": "level", "P": "pressure", "T": "temperature", "A": "analysis", "H": "hand"}
ISA_FUNCTION = {"T": "transmitter", "I": "indicator", "C": "controller", "V": "valve", "A": "alarm", "S": "switch",
                "E": "element", "G": "gauge/glass", "R": "recorder", "Y": "relay", "H": "high", "L": "low"}

# drawing node type -> control-loop role
ROLE = {"transmitter": "sensor", "controller": "controller", "control_valve": "final_element",
        "switch": "trip/alarm", "alarm": "trip/alarm"}


def find_tags(text):
    """All KKS and ISA-shaped tags in text, in order, deduped."""
    hits = [(m.start(), m.group(0)) for rx in (KKS_RE, ISA_RE) for m in rx.finditer(text)]
    return list(dict.fromkeys(t for _, t in sorted(hits)))


def decode(tag):
    if m := KKS_RE.fullmatch(tag):
        unit, system, seq, fn, num, train = m.groups()
        out = {"tag": tag, "scheme": "KKS", "unit": unit, "system": system, "system_seq": seq,
               "function": fn, "number": num, "train": train or None, "family": KKS_FAMILY.get(fn[0], "unknown")}
        if fn[0] in "CDF":
            out["variable"] = KKS_VARIABLE.get(fn[1], f"unknown '{fn[1]}'")
        else:
            out["component"] = KKS_MECHANICAL.get(fn, "unknown")
        return out
    if m := ISA_RE.fullmatch(tag):
        letters, number, suffix = m.groups()
        out = {"tag": tag, "scheme": "ISA", "letters": letters, "number": number, "suffix": suffix or None}
        if letters in ISA_EQUIPMENT:
            return out | {"type": ISA_EQUIPMENT[letters]}
        return out | {"variable": ISA_VARIABLE.get(letters[0], f"unknown '{letters[0]}'"),
                      "functions": [ISA_FUNCTION.get(c, f"unknown '{c}'") for c in letters[1:]]}
    return {"tag": tag, "scheme": "unknown"}


def group_loops(components, links):
    """Control loops = instruments/control valves connected by signal links, named after the controller.
    -> {name: {loop, members: {tag: role}, missing: [roles]}}"""
    adj = {t: set() for t, c in components.items() if c["kind"] in ROLE}
    for l in links:
        if l["relation"] == "signal" and l["from"] in adj and l["to"] in adj:
            adj[l["from"]].add(l["to"])
            adj[l["to"]].add(l["from"])
    loops, seen = {}, set()
    for start in sorted(adj):
        if start in seen:
            continue
        stack, members = [start], {}
        while stack:
            t = stack.pop()
            if t not in seen:
                seen.add(t)
                members[t] = ROLE[components[t]["kind"]]
                stack += adj[t]
        roles = set(members.values())
        missing = []
        if "controller" in roles and "final_element" not in roles:
            missing.append("final_element")
        if "final_element" in roles and "controller" not in roles:
            missing.append("controller")
        if "controller" in roles and "sensor" not in roles:
            missing.append("sensor")
        name = next((t for t, r in sorted(members.items()) if r == "controller"), start)
        loops[name] = {"loop": name, "members": dict(sorted(members.items())), "missing": missing}
    return loops


def loop_of(tag, components, links):
    return next((l for l in group_loops(components, links).values() if tag in l["members"]), None)


if __name__ == "__main__":
    d = decode("20LFC20AA102")
    assert d["scheme"] == "KKS" and d["system"] == "LFC" and d["component"] == "valve / damper", d
    assert decode("20LFC10CP001")["variable"] == "pressure"
    assert decode("20LFC10AT001")["component"].startswith("cleaning")
    assert decode("LV-202")["functions"] == ["valve"] and decode("P-102A")["type"] == "pump"
    assert find_tags("20LFC20AP001 tripped; LV-202 and 20LFC20AP001 again") == ["20LFC20AP001", "LV-202"]
    comps = {"T1": {"kind": "transmitter"}, "C1": {"kind": "controller"}, "V1": {"kind": "control_valve"},
             "T2": {"kind": "transmitter"}, "C2": {"kind": "controller"}, "S1": {"kind": "switch"}, "P1": {"kind": "pump"}}
    links = [{"from": "T1", "to": "C1", "relation": "signal"}, {"from": "C1", "to": "V1", "relation": "signal"},
             {"from": "T2", "to": "C2", "relation": "signal"}, {"from": "S1", "to": "P1", "relation": "signal"}]
    loops = group_loops(comps, links)
    assert loops["C1"]["missing"] == [] and loops["C2"]["missing"] == ["final_element"], loops
    assert loops["S1"]["members"] == {"S1": "trip/alarm"} and "P1" not in str(loops)
    assert loop_of("V1", comps, links)["loop"] == "C1"
    print("tags ok")
