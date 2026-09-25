# Known issues

Open items the authors already consider questionable or unresolved, kept visible on purpose. An
[ERRATA.md](ERRATA.md) entry is a *fixed* error; a known issue is one that is **open, disputed, or a
deliberate won't-fix**. Each entry carries an ID, the paper and section, the statement at issue, a
status, and the reason. Papers reference an item inline as `[KI-…]`.

Status legend: **open** (real, not yet fixed) · **disputed** (evidence points both ways) ·
**wontfix** (acknowledged, deliberately not changed, with a reason) · **tracking** (structural work
item).

| ID | Paper · section | Issue | Status | Reason / plan |
|---|---|---|---|---|
| KI-01 | 03-volatility/L2-vol-surface-vix-complex §7 | The VIX (17.71 on 2026-09-16) is said to sit several points above the "~12% 30-day ATM SPX vol" of Figure 1, explained by skew alone. With VIX9D = 17.40 that day, a 30-day ATM of 12% implies a ~5.4-point skew premium, which is high (typical 2–4). | **open** | Cannot resolve without the licensed, non-redistributed CBOE chain snapshot. Fix: compare the snapshot timestamp and VIX at the *same* instant, recompute ATM-IV from the chain independently (VIX-strip vs ATM straddle), and split the gap into skew and residual. (Audit B12.) |
| KI-02 | research/volatility-managed-strategies | The paper exists as two texts: `*.md` (14 sections, ~6,144 words) and `*.tex`/PDF (9 sections, ~5,455 words). They agree on the *corrected numbers* but differ in structure and length, so every fix must be made twice. | **tracking** | Move to one source: either `md → pandoc → PDF` with a template, or `.tex` as source with `.md` generated from it, and mark the other "draft, superseded". Corrected claims are kept in sync in the interim. (Audit C4.) |
| KI-03 | Reg NMS world-state — 05-market-mechanics/L1-how-markets-move §3.1 | Any anchor on a real-world date (e.g. the Reg NMS half-cent tick compliance date) needs a dated source beside it or an expiry, or the regression guard will freeze a value the world has moved past. | **tracking** | Policy: world-state claims carry a URL + access date in `SOURCES` and are re-checked at each release, not pinned by a text anchor. |
| KI-N10 | series-wide | ~40 open high-severity findings outside K1–K14, referenced in ERRATA (N10) as "a separate work item." A third-party check suite (T19) triaged 23 of them; the full triaged table is the intended seed for this list. | **open** | Import the T19 triage table here (ID, paper, statement, status, reason) and add an inline `[KI-…]` marker in each affected paper. Until imported, the count (~40) is disclosed but the items are not individually listed here. |

## How this list is maintained

- A new finding starts here as **open**. It moves to [ERRATA.md](ERRATA.md) when fixed and verified,
  or to **wontfix** with a written reason.
- An item is only marked fixed once it is reproduced by the repo's own code, an independent
  recomputation, or a primary source — the same bar as ERRATA.
- The count in the README's house rules and this table must agree; a bare "~40 open" with no list is
  what this file exists to prevent.
