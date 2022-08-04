install:
	pip install -e .

install-dev: 
	pip install -r test-requirements.txt

compile:
	pip-compile test-requirements.in
