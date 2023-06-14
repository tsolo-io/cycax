.ONESHELL: # Run all the commands in the same shell

all: install box fan

main:
	. ./.venv/bin/activate
	pip install --force-reinstall $(shell ls ${PWD}/../cycax/dist/cycax-*.whl | sort | head -n1)
	./main.py

box:
	. ./.venv/bin/activate
	pip install --force-reinstall $(shell ls ${PWD}/../cycax/dist/cycax-*.whl | sort | head -n1)
	./box_with_concubes.py

fan:
	. ./.venv/bin/activate
	pip install --force-reinstall $(shell ls ${PWD}/../cycax/dist/cycax-*.whl | sort | head -n1)
	./fan_example.py

install:
	test -d ./.venv || python3 -m venv ./.venv
	. ./.venv/bin/activate                                                                                                                                                                       
	pip install stl matplotlib
	chmod a+x *.py
