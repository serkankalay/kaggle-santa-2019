.PHONY: clean format init

init:
	poetry install

clean:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

format:
	black santa_19 tests
	isort santa_19 tests

test-all:
	tox --parallel auto
