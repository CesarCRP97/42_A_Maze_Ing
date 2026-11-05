ifeq ($(OS),Windows_NT)
    VENV_PYTHON = .venv/Scripts/python.exe
    VENV_PIP = .venv/Scripts/pip.exe
    PYTHON = $(VENV_PYTHON)
    PIP = $(VENV_PIP)
    RM = rmdir /s /q
    RMDIRS = rmdir /s /q
else
    VENV_PYTHON = .venv/bin/python
    VENV_PIP = .venv/bin/pip
    PYTHON = $(VENV_PYTHON)
    PIP = $(VENV_PIP)
    RM = rm -rf
    RMDIRS = rm -rf
endif

.PHONY: venv install run debug clean lint test demo check

venv:
	@test -d .venv || python -m venv .venv

install: venv
	$(PIP) install -e .[dev]

run: install
	$(PYTHON) a_maze_ing.py config.txt

debug: install
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	$(RMDIRS) __pycache__ 2>nul || true
	$(RMDIRS) mazegen/__pycache__ 2>nul || true
	$(RMDIRS) tests/__pycache__ 2>nul || true
	$(RMDIRS) visualizer/__pycache__ 2>nul || true
	$(RMDIRS) .mypy_cache 2>nul || true
	$(RMDIRS) .pytest_cache 2>nul || true
	$(RMDIRS) build 2>nul || true
	$(RMDIRS) dist 2>nul || true
	$(RM) *.egg-info 2>nul || true
	$(RM) *.whl 2>nul || true
	$(RM) *.tar.gz 2>nul || true

lint: install
	$(PYTHON) -m flake8 . --exclude=.venv
	$(PYTHON) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs . --exclude=.venv

test: install
	$(PYTHON) -m tests.test_visualizer
	$(PYTHON) -m tests.test_generator
	$(PYTHON) -m tests.test_maze
	$(PYTHON) -m tests.test_config_parser
	$(PYTHON) -m tests.test_pattern42

demo: install
	$(PYTHON) -m tests.test_visualizer --demo

check: run
