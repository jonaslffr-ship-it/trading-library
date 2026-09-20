# Trading Library — reproducibility targets.
# Point PY at a Python with numpy + matplotlib + scipy, e.g.:
#   make figures PY="C:/path/to/.venv/Scripts/python.exe"
#   make verify  PY="C:/path/to/.venv/Scripts/python.exe"
PY ?= python
FIGS := $(shell find . -path '*/figures/*.py' -not -path './.git*' | sort)

.PHONY: figures verify help
help:
	@echo "make figures  - regenerate every figure from cached free data"
	@echo "make verify   - run the offline reproducibility harness (OK/SKIP/FAIL per script)"
	@echo "Set PY=... to the interpreter (needs numpy, matplotlib, scipy)."

figures:
	@for f in $(FIGS); do \
	  echo ">> $$f"; \
	  ( cd $$(dirname $$f) && $(PY) $$(basename $$f) ) || exit $$?; \
	done
	@echo "All figures rebuilt. (fig_case_r_dist skips itself unless the private ES trade list is present.)"

verify:
	@echo "== 1/3  paper listings run verbatim and reproduce printed numbers =="
	@$(PY) verify_listings.py
	@echo "== 2/3  corrected claims re-derived vs the paper's numbers =="
	@$(PY) prove_fixes.py
	@echo "== 3/3  every figure reproduces offline =="
	@PY="$(PY)" bash verify_repro.sh
