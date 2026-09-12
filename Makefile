FOLDER_NAME = night-shift@christophermca.github.io
SRC_DIR=src/

ZIP_FILE := $(FOLDER_NAME)
ZIP_FILE := $(addsuffix .zip,$(ZIP_FILE))

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))


.PHONY: all
all:
	@echo "ZIP_FILE: '$(ZIP_FILE)'"
	@echo "FOLDER_NAME: '$(FOLDER_NAME)'"
	@echo "MAKEFILE_DIR: '$(MAKEFILE_DIR)'"


.PHONY: test
test:
	 virtualenv venv && \
	. venv/bin/activate &&\
	pip install -U pytest \
	requests pycairo PyGObject &&\
	python -m pytest tests -c pytest.ini
