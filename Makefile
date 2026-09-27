PROJECT_NAME:=gnome-night-shift
PATH_TO_SCHEMA_FILE:="$(HOME)/.local/share"
.PHONY: test
test:
	 virtualenv venv && \
	. venv/bin/activate &&\
	pip install -U pytest \
	requests pycairo PyGObject &&\
	python -m pytest tests -c pytest.ini

.PHONY: test
test-nocov:
	 virtualenv venv && \
	. venv/bin/activate &&\
	pip install -U pytest \
	requests pycairo PyGObject &&\
	python -m pytest tests -c pytest.ini --no-cov

build:
	source venv/bin/activate &&\
	python -m build

rebuild:
	rm -rf dist/ &&\
	$(MAKE) build

publish-testpypi: rebuild
	source venv/bin/activate &&\
	twine upload --repository testpypi dist/*

install:
	python -m pip install --index-url https://test.pypi.org/simple/ $(PROJECT_NAME)

install-dev:
	python -m pip install -e .

comile-schema:
	cd $(PATH_TO_SCHEMA_FILE) &&\
	glib-compile-schemas .

edit-schema:
	GSETTINGS_SCHEMA="$(PATH_TO_SCHEMA_FILE)" dconf-editor
