.ONESHELL: # Run all the commands in the same shell
.PHONY: docs
.DEFAULT_GOAL := help

help:
	@echo "Help"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build:  ## Build a test version of CyCAx
	find dist -type f | sort | tail -n+5 | xargs rm -f
	hatch version "$(shell hatch version | cut -d. -f1,2).$(shell date +%s)"
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
