.ONESHELL: # Run all the commands in the same shell
.PHONY: docs

build:
	hatch build

test:
	hatch run test

format:
	hatch run lint:fmt

docs:
	hatch run docs:build

docs-serve:
	hatch run docs:serve
