.PHONY: help format lint test build clean setup, setup_name, version

SHELL := /bin/bash

SOURCE_DIR := src
TEST_DIR := test
CODE_DIRS := $(SOURCE_DIR) $(TEST_DIR)
BUILD_DIRS := dist
PYTHON := python3

#HELP help : prints out information about available makefile commands
help:
	@sed -n 's/^#HELP//p' Makefile

#HELP format : automatically reformats the respository code
format:
	black $(CODE_DIRS)

#HELP lint : runs automated code style checks
lint:
	ruff $(CODE_DIRS)

#HELP test : runs developer written code tests
test:
	$(PYTHON) -m pytest $(TEST_DIR)

#HELP build : packages up repository code
build:
	$(PYTHON) -m build --sdist .

#HELP clean : deletes built resources
clean:
	$(RM) -rf $(BUILD_DIRS)

#HELP setup : run this when starting a new project to change the project name and version
setup: setup_name version
	@echo "Please modify the metadata in setup.cfg"

setup_name:
	@read -p "New package name: " package_name; \
	read -p "Apply change? [y\N]: " confirmation; \
	if [[ $$confirmation =~ [Yy]([Ee][Ss])? ]]; then \
		mv "$(SOURCE_DIR)/python_package_template" "$(SOURCE_DIR)/$${package_name}"; \
		mv "$(TEST_DIR)/python_package_template" "$(TEST_DIR)/$${package_name}"; \
		sed -i "s/python_package_template/$${package_name}/g" setup.cfg; \
		sed -i "s/python_package_template/$${package_name}/g" "$(TEST_DIR)/$${package_name}/test_version.py"; \
		echo "Package name changed to $${package_name}"; \
	else \
		echo "No change applied to package name"; \
	fi; \
	echo

#HELP version : changes the package version
version:
	@echo -n "Current version: "; \
	version_file=$$(find src -name VERSION | head -n 1); \
	current_version=$$(cat "$${version_file}"); \
	echo "$${current_version}"; \
	read -p "New version: " new_version; \
	read -p "Apply change? [y\N]: " confirmation; \
	check="[Yy]([Ee][Ss])?"; \
	if [[ "$${confirmation}" =~ $${check} ]]; then \
		sed -i "s/$${current_version}/$${new_version}/g" "$${version_file}"; \
		echo "Change applied, version set to: $$(cat "$${version_file}")"; \
	else \
		echo "Not applying any changes to the version"; \
	fi; \
	echo
