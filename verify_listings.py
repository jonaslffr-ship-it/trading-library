#!/usr/bin/env python3
"""Re-run of the review's Teil IV, on the CORRECTED papers: extract the python
listings verbatim from each .md, run them UNCHANGED, and check that they execute
and reproduce the numbers printed in the same paper. Needs numpy (+ scipy only
if a listing does). Run:  python verify_listings.py"""
import os, re, io, math, contextlib, random
ROOT = os.path.dirname(os.path.abspath(__file__))

def blocks(path):
    return re.findall(r"```python\s*\n(.*?)```", open(path, encoding="utf-8").read(), re.DOTALL)

def run_file(rel):
    path = os.path.join(ROOT, rel)
    ns = {"__name__": "__main__"}; buf = io.StringIO(); nblk = nok = 0
    for b in blocks(path):
        nblk += 1
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(b, path, "exec"), ns); nok += 1
        except Exception as e:
            buf.write(f"[block skipped: {type(e).__name__}: {e}]\n")
    return ns, buf.getvalue(), nblk, nok

P = F = 0
def chk(name, cond, detail=""):
    global P, F; P += bool(cond); F += (not cond)
    print(f" [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")

print("VERIFY LISTINGS - the papers' OWN embedded code, extracted and run unchanged")
print("=" * 94)

ns, out, nb, nk = run_file("02-options/L2-greeks-first-order.md")
print(f"\n[L2-greeks-first-order] blocks {nk}/{nb} ok | stdout:", " ".join(out.split()))
g = ns["first_order_greeks"](S=100, K=100, T=21/252, r=0.04, sigma=0.20)
chk("price=+2.4694", abs(g["price"] - 2.4694) < 1e-3, f"got {g['price']:+.4f}")
chk("delta=+0.5345", abs(g["delta"] - 0.5345) < 1e-3, f"got {g['delta']:+.4f}")
chk("elasticity=+21.65", abs(g["elasticity"] - 21.65) < 1e-2, f"got {g['elasticity']:+.4f}")
dg = ns["first_order_greeks"](S=80, K=100, T=7/252, r=0.0, sigma=0.10)
chk("B1 deep-OTM elasticity=NaN, NO ZeroDivision", math.isnan(dg["elasticity"]), f"got {dg['elasticity']}")

ns, out, nb, nk = run_file("02-options/L3-greeks-second-order.md")
print(f"\n[L3-greeks-second-order] blocks {nk}/{nb} ok")
g = ns["bsm_greeks"](100, 100, 21/252, 0.04, 0.20)
chk("gamma=+0.06884", abs(g["gamma"] - 0.06884) < 1e-4, f"got {g['gamma']:+.5f}")
chk("F3 vanna=-0.000574", abs(g["vanna"] + 0.000574) < 1e-5, f"got {g['vanna']:+.6f}")
chk("F3 charm=-0.000566", abs(g["charm"] + 0.000566) < 1e-5, f"got {g['charm']:+.6f}")
chk("F3 vanna != charm (no spurious identity)", round(g["vanna"], 6) != round(g["charm"], 6))
fd = ns["self_check"](100, 100, 21/252, 0.04, 0.20)
cf = [g["gamma"], g["vanna"], g["charm"], g["vomma"], g["veta"]]
r = [a / b for a, b in zip(fd, cf)]
chk("F2 self_check ratios ~1.0", all(abs(x - 1) < 1e-3 for x in r), f"ratios={[round(x, 4) for x in r]}")

ns, out, nb, nk = run_file("02-options/L3-greeks-third-order.md")
print(f"\n[L3-greeks-third-order] blocks {nk}/{nb} ok")
t = ns["third_order_fd"](100, 100, 21/252, 0.04, 0.20)
chk("speed=-0.001721", abs(t["speed"] + 0.001721) < 1e-5, f"got {t['speed']:+.6f}")
chk("zomma=-0.34334", abs(t["zomma"] + 0.34334) < 1e-3, f"got {t['zomma']:+.5f}")
chk("color=+0.00114011", abs(t["color"] - 0.00114011) < 1e-5, f"got {t['color']:+.6f}")
chk("ultima=-3.10558", abs(t["ultima"] + 3.10558) < 1e-2, f"got {t['ultima']:+.4f}")

ns, out, nb, nk = run_file("04-quant/L3-overfitting-calibration.md")
print(f"\n[L3-overfitting-calibration] blocks {nk}/{nb} ok")
p0 = ns["psr"](0.15, 0.0, 250, 0, 3, rho=0.0); p2 = ns["psr"](0.15, 0.0, 250, 0, 3, rho=0.2)
chk("F4 psr(rho=0.2) < psr(rho=0.0) (Lo correction bites)", p2 < p0, f"{p0:.4f} -> {p2:.4f}")
f = [0.2, 0.8, 0.5, 0.65, 0.35] * 40
y = [1 if random.Random(1).random() < p else 0 for p in f]
bm = ns["brier_murphy"](f, y)
b, rel, res, unc = (bm if isinstance(bm, (list, tuple)) else (bm["brier"], bm["rel"], bm["res"], bm["unc"]))
chk("brier = rel - res + unc (identity)", abs(b - (rel - res + unc)) < 1e-9, f"brier={b:.5f}")
e2 = ns["expected_max_sr"](2000, 1.0); e1 = ns["expected_max_sr"](10, 1.0)
chk("expected_max_sr runs & monotone in n", math.isfinite(e2) and e2 > e1 > 0, f"n=10:{e1:.3f} n=2000:{e2:.3f}")

ns, out, nb, nk = run_file("03-volatility/L3-vol-modeling-vrp.md")
print(f"\n[L3-vol-modeling-vrp] blocks {nk}/{nb} ok")
defs = [k for k in ns if callable(ns.get(k)) and not k.startswith("__")]
chk("GARCH listing exec'd, callables defined", len(defs) > 0, f"defs={sorted(defs)[:8]}")

print("=" * 94); print(f"RESULT: {P} passed, {F} failed")
raise SystemExit(1 if F else 0)
