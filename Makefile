.ONESHELL: # Run all the commands in the same shell
.PHONY: docs

build:
	find dist -type f | sort | tail -n+5 | xargs rm -f
	hatch version "$(shell hatch version | cut -d. -f1,2).$(shell date +%s)"
	hatch build

test:
	hatch run cov

format:
	hatch run lint:fmt

docs:
	hatch run docs:build

docs-serve:
	hatch run docs:serve
