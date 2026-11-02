PYTHON=python3

.PHONY: install run debug clean lint

install:
	$(PYTHON) -m pip install .

run:
	$(PYTHON) a_maze_ing.py config.txt

debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache

lint:
	$(PYTHON) -m flake8 --ignore= .
