init:
	uv sync

devel:
	uv sync --all-extras
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push --install-hooks -t post-checkout -t post-merge

test:
	uv run pytest tests -v

analysis: # Lint, format, import optimizer, etc.
	uv run pre-commit run --all-files

install:
	uv pip install --upgrade .

dist:
	uv build

clean:
	$(RM) -fr .tox/
	$(RM) -fr build/ dist/ *.egg-info
	find . -iname *.pyc -exec rm -f {} +
	uv pip uninstall -y pyetrade
