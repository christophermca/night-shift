
MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))


.PHONY: test
test:
	 virtualenv venv && \
	. venv/bin/activate &&\
	pip install -U pytest \
	requests pycairo PyGObject &&\
	python -m pytest tests -c pytest.ini
