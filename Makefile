# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

.ONESHELL: # Run all the commands in the same shell
.PHONY: docs examples
.DEFAULT_GOAL := help

help:
	@echo "Help"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build:  ## Build a test version of CyCAx
	hatch build

test: ## Run unit tests
	hatch run test-not-slow

test-all: ## Run all the tests
	hatch run test

test-ci:
	hatch run cov

format:  ## Format the code
	hatch run lint:fmt

spelling:  ## Show spelling mistakes in the code
	hatch run lint:spell

docs:  ## Create documentation
	hatch run docs:build

docs-serve:  ## Run a server for documentation
	hatch run docs:serve

docs-open:  ## Open the documentation
	xdg-open ./docs/site/index.html

parts:
	hatch run python ./src/cycax/parts/main.py

examples:
	mkdir -p ./build
	hatch run python3 ./src/examples/beveled_edges.py
	hatch run python3 ./src/examples/box.py
	hatch run python3 ./src/examples/box_with_concubes.py
	hatch run python3 ./src/examples/thlob_example.py
	hatch run python3 ./src/examples/gear_factory.py

example/gear:
	hatch run python3 ./src/examples/gear_factory.py
