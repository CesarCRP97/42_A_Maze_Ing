PYTHON = python3
PIP = pip

.PHONY: install run debug clean lint

install:
	$(PIP) install flake8 mypy pytest build setuptools wheel

run:
	$(PYTHON) a_maze_ing.py config.txt

debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	rm -rf __pycache__ */__pycache__ .mypy_cache .pytest_cache build dist *.egg-info *.whl *.tar.gz

lint:
	flake8 .
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .
