PROJECT_NAME := noc-shift
GNOME_NAME   := gnome-night-shift
INDEXES      := --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
SCHEMA_DIR   := src/night_shift/schemas
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

.PHONY: dev test test-nocov build rebuild publish-testpypi install install-dev upgrade-dev compile-schema edit-schema

dev: $(PY)
	$(PY) -m pip install -e ".[test,dev]" -e ./gnome-night-shift

test: dev
	$(PY) -m pytest -c pytest.ini

test-nocov: dev
	$(PY) -m pytest -c pytest.ini --no-cov

build: $(PY)
	$(PY) -m pip install -U build
	$(PY) -m build . --outdir dist/
	$(PY) -m build gnome-night-shift --outdir dist/

rebuild:
	rm -rf dist/
	$(MAKE) build

publish-testpypi: rebuild
	$(PY) -m pip install -U twine
	$(PY) -m twine upload --repository testpypi dist/*

install:
	$(PY) -m pip install $(INDEXES) $(GNOME_NAME)

install-global:
	sudo pipx install --global --system-site-packages --pip-args="$(INDEXES)" $(GNOME_NAME)

install-dev: dev

upgrade-dev: $(PY)
	$(PY) -m pip install --upgrade .

compile-schema:
	glib-compile-schemas $(SCHEMA_DIR)

edit-schema:
	GSETTINGS_SCHEMA_DIR="$(SCHEMA_DIR)" dconf-editor
