# Contributing

Contributions should preserve the safety contract.

Do not add code that executes mutating commands such as:

- `brew install`
- `brew uninstall`
- `brew upgrade`
- `brew update`
- `rm`
- `mv`
- `cp`

Run checks locally:

```bash
pip install -e ".[dev]"
pytest
ruff check .
```
