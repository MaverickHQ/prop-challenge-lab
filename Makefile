.PHONY: test lint check data build-CampaignFunction

test:
	python3 -m pytest

lint:
	python3 -m ruff check occams/ tests/ scripts/

check:
	python3 -m pytest
	python3 -m ruff check occams/ tests/ scripts/
	python3 -m occams.privacy
	python3 -m occams.charset

data:
	@echo "Buy MES.v.0 + MNQ.v.0 ohlcv-1m from Databento -> data/MES.csv, data/MNQ.csv (P1)"

paper-morning:  ## protocol #4 morning card (cron 09:00 ET weekdays)
	python3 scripts/paper_morning.py

paper-evening:  ## protocol #4 debrief + parity (cron 17:00 ET weekdays)
	python3 scripts/paper_evening.py

# SAM `BuildMethod: makefile` target. An ALLOW-LIST, deliberately: only
# these paths ship. The guard below is not belt-and-braces, it is the
# check that caught a 533 MB artifact carrying licensed bars, the API key
# and the venue name when SAM's default builder swept the whole repo.
build-CampaignFunction:
	mkdir -p $(ARTIFACTS_DIR)/aws
	cp -r occams $(ARTIFACTS_DIR)/occams
	cp aws/*.py $(ARTIFACTS_DIR)/aws/
	python3 -m pip install -q -r requirements.txt -t $(ARTIFACTS_DIR) \
		--platform manylinux2014_aarch64 --only-binary=:all: \
		--python-version 3.12 --implementation cp
	find $(ARTIFACTS_DIR) -name '__pycache__' -type d -prune -exec rm -rf {} +
	find $(ARTIFACTS_DIR) -name '*.pyc' -delete
	python3 scripts/check_artifact.py $(ARTIFACTS_DIR)

reproduce:                ## re-score REAL archived results end to end (~12 min: Z0 re-simulates 1,741 days x 2)
	python3 -m pytest tests/test_reproduction.py -m reproduction -q

.PHONY: reproduce

quickstart:               ## $0 controls demo — no data, no keys, no network
	python3 scripts/quickstart.py

plots:                    ## regenerate the published figures from the register
	python3 scripts/make_plots.py

report:                   ## F1 — render the research console from the register
	python3 scripts/build_report.py

report-offline:           ## same, from artifacts/register-cache.json (no network)
	python3 scripts/build_report.py --offline

.PHONY: quickstart plots report report-offline
