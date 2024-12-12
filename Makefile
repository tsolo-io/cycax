.ONESHELL: # Run all the commands in the same shell
.PHONY: docs

build:
	hatch build

test:
	hatch run test-not-slow

test-all:
	hatch run test

test-ci:
	hatch run cov

format:
	hatch run lint:fmt

spelling:
	hatch run lint:spell

docs:
	hatch run docs:build

docs-serve:
	hatch run docs:serve

docs-open:
	xdg-open ./docs/site/index.html

parts:
	hatch run python ./src/cycax/parts/main.py
