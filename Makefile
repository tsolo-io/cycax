.ONESHELL: # Run all the commands in the same shell
.PHONY: docs

build:
	find dist -type f | sort | tail -n+5 | xargs rm -f
	hatch version "$(shell hatch version | cut -d. -f1,2).$(shell date +%s)"
	hatch build

test:
	hatch run test-not-slow

test-all:
	hatch run test

test-ci:
	hatch run cov

format:
	hatch run lint:fmt

selling:
	hatch run lint:spell

docs:
	hatch run docs:build

docs-serve:
	hatch run docs:serve

docs-open:
	xdg-open ./docs/site/index.html

parts:
	hatch run python ./src/cycax/parts/main.py
