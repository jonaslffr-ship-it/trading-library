# NOTICE

This repository ("Trading Library" by Jonas Löffler) contains only original
work by the author:

- the L1/L2/L3 papers (Markdown + PDF, English and German) and their figures,
  licensed CC BY 4.0 (see `LICENSE`);
- the accompanying source code (figure scripts, research package), licensed
  MIT (see `LICENSE-CODE`).

No third-party study PDFs are redistributed in this repository. External works
are referenced only by citation within the papers and remain under the rights
of their original authors and publishers.

## Data

Free, publicly downloadable daily-history CSVs (e.g. CBOE `VIX_History.csv`)
are included under `*/figures/data/` for offline reproducibility. Licensed
intraday option-chain snapshots (CBOE delayed-quote chains, optionsDX
end-of-day chains) are NOT redistributed; they are git-ignored and re-fetched
by the figure scripts at run time under each vendor's own terms of use. See the
"Data license" section of `README.md` and
`research/volatility-managed-strategies/data/data_manifest.csv`.
