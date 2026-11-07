PROJECT_NAME := nocturne-shift
TESTPYPI     := https://test.pypi.org/simple/
WHEELS       := build/testpypi-wheels
# Pin a version with: make install NOCTURNE_SHIFT=nocturne-shift==0.5.3
NOCTURNE_SHIFT ?= nocturne-shift
SCHEMA_DIR   := src/nocturne_shift/schemas
VENV         := venv
PYTHON       ?= python3
PY           := $(VENV)/bin/python

# Each recipe line runs in its own shell, so `. venv/bin/activate` can't carry
# over to other targets. Call the venv's python directly instead.
# --system-site-packages reuses the distro's PyGObject/pycairo (building them
# with pip needs the C headers for cairo and gobject-introspection).
$(PY):
	$(PYTHON) -m venv --system-site-packages $(VENV)
	$(PY) -m pip install -U pip

# .PHONY: dev test test-nocov build rebuild publish-testpypi install install-dev upgrade-dev compile-schema edit-schema
.PHONY: dev test test-nocov build rebuild publish-testpypi testpypi-wheels install install-dev upgrade-dev compile-schema edit-schema

dev: $(PY)
	$(PY) -m pip install -e ".[test, dev]"

test: dev
	$(PY) -m pytest -c pytest.ini

test-nocov: dev
	$(PY) -m pytest -c pytest.ini --no-cov

build: $(PY)
	$(PY) -m pip install -U build
	$(PY) -m build . --outdir dist/

rebuild:
	rm -rf dist/
	$(MAKE) build

publish-testpypi: rebuild
	$(PY) -m pip install -U twine
	$(PY) -m twine upload --repository testpypi dist/*

testpypi-wheels: $(PY)
	rm -rf $(WHEELS)
	$(PY) -m pip download --no-deps --only-binary=:all: \
		--index-url $(TESTPYPI) --dest $(WHEELS) "$(NOCTURNE_SHIFT)"

# Install the downloaded wheel file; its dependencies come from PyPI only
install: testpypi-wheels
	$(PY) -m pip install $(WHEELS)/nocturne_shift-*.whl

install-global: testpypi-wheels
	sudo pipx install --global --system-site-packages $(abspath $(WHEELS))/nocturne_shift-*.whl

install-dev: dev

upgrade-dev: $(PY)
	$(PY) -m pip install --upgrade .

compile-schema:
	glib-compile-schemas $(SCHEMA_DIR)

edit-schema:
	GSETTINGS_SCHEMA_DIR="$(SCHEMA_DIR)" dconf-editor
