SHELL=/bin/bash -eu -o pipefail


requirements.txt:
	curl -sL $@ https://raw.githubusercontent.com/getsentry/sentry/51281a6abd8ff4a93d2cebc04e1d5fc7aa9c4c11/requirements-base.txt | grep -v -- --index-url > $@

.github/workflows/benchmark.yml: Makefile bin/build_workflow.sh templates/workflow_start.yml templates/workflow_tool.yml templates/workflow_end.yml
	./bin/build_workflow.sh > $@

.PHONY: github-workflow
github-workflow: .github/workflows/benchmark.yml

# random package to benchmark adding a new dependency
PACKAGE := goodconf

.PHONY: pip-clean

TOOLS := "$(TOOLS) pip"
.PHONY: pip-tooling pip-import pip-clean-cache pip-clean-venv pip-clean-lock pip-lock pip-install pip-add-package pip-version
pip-tooling:
	echo
pip-import:
	cat requirements.txt
pip-clean-cache: pip-clean
	rm -rf ~/.cache/pip
pip-clean-venv:
	rm -rf pip/.venv
pip-clean-lock:
	echo
pip-lock:
	echo
pip-install:
	test -f pip/.venv/bin/python || python3 -m venv --upgrade-deps pip/.venv
	test -f pip/.venv/bin/wheel || pip/.venv/bin/python -m pip install -U wheel
	pip/.venv/bin/pip install -r requirements.txt
pip-update:
	echo
pip-add-package:
	echo
pip-version:
	@pip --version | awk '{print $$3}'

TOOLS := poetry
.PHONY: poetry-tooling poetry-import poetry-clean-cache poetry-clean-venv poetry-clean-lock poetry-lock poetry-install poetry-add-package poetry-version
poetry-tooling:
	pipx install poetry
	poetry config virtualenvs.in-project true
poetry-import:
	cd poetry; poetry add $$(sed -e 's/#.*//' -e '/^$$/ d' < ../requirements.txt)
poetry-clean-cache: pip-clean
	rm -rf ~/.cache/pypoetry
poetry-clean-venv:
	cd poetry; poetry env remove --all || true
poetry-clean-lock:
	rm -f poetry/poetry.lock
poetry-lock:
	cd poetry; poetry lock --no-update
poetry-install:
	cd poetry; poetry install
poetry-update:
	cd poetry; poetry update
poetry-add-package:
	cd poetry; poetry add $(PACKAGE)
poetry-version:
	@poetry --version | awk '{print $$3}' | tr -d ')'

TOOLS := "$(TOOLS) pdm"
.PHONY: pdm-tooling pdm-import pdm-clean-cache pdm-clean-venv pdm-clean-lock pdm-lock pdm-install pdm-add-package pdm-version
pdm-tooling:
	curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 -
pdm-import:
	cd pdm; pdm import -f requirements ../requirements.txt
pdm-clean-cache: pip-clean
	rm -rf ~/.cache/pdm
pdm-clean-venv:
	rm -rf pdm/.venv pdm/__pypackages__
	mkdir -p pdm/__pypackages__
pdm-clean-lock:
	rm -f pdm/pdm.lock
pdm-lock:
	cd pdm; pdm lock
pdm-install:
	cd pdm; pdm install
pdm-update:
	cd pdm; pdm update
pdm-add-package:
	cd pdm; pdm add $(PACKAGE)
pdm-version:
	@pdm --version | awk '{print $$3}'

TOOLS := "$(TOOLS) uv"
.PHONY: uv-tooling uv-import uv-clean-cache uv-clean-venv uv-clean-lock uv-lock uv-install uv-add-package uv-version
uv-tooling:
	pip install --user uv
uv-import:
	cd uv; uv add --frozen -r ../requirements.txt
uv-clean-cache:
	rm -rf ~/.cache/uv
uv-clean-venv:
	rm -rf uv/.venv
uv-clean-lock:
	rm -f uv/uv.lock
uv-lock:
	cd uv; uv lock
uv-install:
	cd uv; uv sync
uv-update:
	cd uv; uv lock --upgrade
uv-add-package:
	cd uv; uv add $(PACKAGE)
uv-version:
	@uv --version | awk '{print $$2}'

TOOLS := "$(TOOLS) uv-old"
.PHONY: uv-old-tooling uv-old-import uv-old-clean-cache uv-old-clean-venv uv-old-clean-lock uv-old-lock uv-old-install uv-old-add-package uv-old-version
uv-old-tooling:
	pip install --user uv
uv-old-import:
	cd uv-old; uv venv
uv-old-clean-cache:
	rm -rf ~/.cache/uv
uv-old-clean-venv:
	rm -rf uv-old/.venv
uv-old-clean-lock:
	rm -f uv-old/requirements.txt
uv-old-lock:
	cd uv-old; uv pip compile --generate-hashes --output-file=requirements.txt ../requirements.txt
uv-old-install:
	cd uv-old; uv venv
	cd uv-old; uv pip sync requirements.txt
uv-old-update:
	cd uv-old; uv pip compile --output-file=requirements.txt ../requirements.txt
	cd uv-old; uv pip sync requirements.txt
uv-old-install-lock:
	cd uv-old; uv venv
	cd uv-old; uv pip install -r requirements.txt
uv-old-add-package:
	echo $(PACKAGE) >> requirements.txt
	$(MAKE) uv-old-lock uv-old-install
uv-old-version:
	@uv --version | awk '{print $$2}'

.PHONY: tools
tools:
	@echo $(TOOLS)
