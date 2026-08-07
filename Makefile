# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

.PHONY: docs examples build
-include .tidy/*.mk

build:  ## Build a test version of CyCAx
	hatch build

test: ## Run unit tests
	hatch run testing:test-not-slow

test-all: ## Run all the tests
	hatch run testing:test

test-ci:
	hatch run testing:ci

format:  ## Format the code
	hatch run lint:fmt

spelling:  ## Show spelling mistakes in the code
	hatch run lint:spell

parts:
	hatch run python ./src/cycax/parts/main.py

examples:
	mkdir -p ./build
	hatch run python3 ./src/examples/beveled_edges.py
	hatch run python3 ./src/examples/box.py
	hatch run python3 ./src/examples/box_with_concubes.py
	hatch run python3 ./src/examples/thlob_example.py
	hatch run python3 ./src/examples/gear_factory.py

example/assemblies:
	hatch run python3 ./src/examples/assemblies.py

example/gear:
	hatch run python3 ./src/examples/gear_factory.py

example/box:
	hatch run python3 ./src/examples/box_with_concubes.py

example/vents:
	hatch run python3 ./src/examples/vents.py

example/thlob:
	hatch run python3 ./src/examples/thlob_example.py

example/flange:
	hatch run python3 ./src/examples/flange.py
