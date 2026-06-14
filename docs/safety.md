# Safety

`brew-adoption-audit` is intentionally read-only.

It does not run mutating Homebrew or filesystem operations. The command runner sets `HOMEBREW_NO_AUTO_UPDATE=1` for every Homebrew metadata call.

Allowed command classes:

- `which brew`
- `mdls ...`
- `brew list --cask`
- `brew search --casks`
- `brew info --json=v2 --cask <cask>`

Forbidden command classes:

- `brew install`
- `brew uninstall`
- `brew upgrade`
- `brew update`
- `brew cleanup`
- `rm`
- `mv`
- `cp`

The only optional write operation is exporting a report through `--output`.
