# brew-adoption-audit

`brew-adoption-audit` is a read-only macOS audit tool that compares installed `.app` bundles with Homebrew cask metadata and produces a conservative adoption plan.

It is designed for developers and administrators who want to identify which manually installed macOS applications are credible candidates for:

```bash
brew install --cask --adopt <cask>
```

The tool **does not execute adoption**. It only prints or exports a report.

## Safety contract

This project is audit-only.

It **will not**:

- install software
- uninstall software
- adopt software
- run `brew update`
- run `brew upgrade`
- run `brew cleanup`
- modify `/Applications`
- modify `~/Applications`
- modify `~/Library`
- modify Homebrew state
- move, copy, rename, or delete application bundles

The only optional write operation is report export through `--output`.

Generated adoption commands are **command previews only**. The user must review and execute them manually.

## What the tool checks

For each discovered `.app` bundle, the tool reads:

- application name
- `.app` bundle name
- bundle identifier
- version
- App Store receipt status
- installed Homebrew cask status
- possible Homebrew cask candidates
- verified cask artifact match
- recommendation and confidence score

A `SAFE_TO_ADOPT` recommendation requires a verified `.app` artifact match from Homebrew cask metadata. A cask candidate alone is not enough.

## Requirements

- macOS
- Python 3.14+
- Homebrew installed and available in `PATH`

## Installation for local development

```bash
git clone https://github.com/pospanet/brew-adoption-audit.git
cd brew-adoption-audit
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If your `python3` already points to Python 3.14+, this is also fine:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## VS Code / Devin Desktop setup

The recommended local layout is:

```text
brew-adoption-audit/
├── .venv/
├── .vscode/
├── brew_adoption_audit/
├── tests/
└── pyproject.toml
```

Recommended `.vscode/settings.json`:

```json
{
  "python.terminal.activateEnvironment": true,
  "python.analysis.autoImportCompletions": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

Do not hard-code `python.defaultInterpreterPath` if the workspace must stay cross-platform. On macOS/Linux the interpreter is usually `.venv/bin/python`; on Windows it is `.venv\\Scripts\\python.exe`.

Recommended `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff"
  ]
}
```

## Usage

Default table output:

```bash
brew-adoption-audit
```

Equivalent explicit form:

```bash
brew-adoption-audit --format table
```

Audit both `/Applications` and `~/Applications`:

```bash
brew-adoption-audit --include-user-applications
```

Audit a specific application directory:

```bash
brew-adoption-audit --applications-dir /Applications
```

Audit multiple directories:

```bash
brew-adoption-audit \
  --applications-dir /Applications \
  --applications-dir "$HOME/Applications"
```

Show read-only commands being executed:

```bash
brew-adoption-audit --verbose
```

Show version:

```bash
brew-adoption-audit --version
```

## CLI arguments

| Argument | Description |
|---|---|
| `--applications-dir PATH` | Directory containing `.app` bundles. Can be repeated. Defaults to `/Applications`. |
| `--include-user-applications` | Also audit `~/Applications`. |
| `--format table\|json\|csv\|markdown\|html` | Output format. Defaults to `table`. |
| `--output PATH` | Optional report output path. This is the only supported write operation. |
| `--verbose` | Print read-only commands to stderr. |
| `--version` | Print tool version and exit. |

## Output formats

### Table

```bash
brew-adoption-audit --format table
```

Human-readable terminal output. In table mode the tool also prints safe-to-adopt command previews and manual-review notes.

### JSON

```bash
brew-adoption-audit --format json --output report.json
```

Useful for automation, inspection, or later processing.

### CSV

```bash
brew-adoption-audit --format csv --output report.csv
```

Useful for spreadsheets and inventory workflows.

### Markdown

```bash
brew-adoption-audit --format markdown --output report.md
```

Useful for PRs, issues, notes, and documentation.

### HTML

```bash
brew-adoption-audit --format html --output report.html
```

Useful for sharing a simple static report.

## Recommendations

The tool emits one of these recommendations:

| Recommendation | Meaning |
|---|---|
| `LEAVE_APP_STORE` | Application appears to be installed from the Mac App Store. Keep App Store as update source. |
| `ALREADY_BREW` | Application is already managed by a Homebrew cask. |
| `SAFE_TO_ADOPT` | A Homebrew cask was found and its `.app` artifact matches the installed app bundle. |
| `MANUAL_REVIEW` | A possible cask exists, but the tool cannot safely prove adoption suitability. |
| `NO_CASK_FOUND` | No credible Homebrew cask candidate was found. |

Example table result:

```text
app_name       app_bundle              verified_cask       confidence  recommendation
-------------  ----------------------  ------------------  ----------  ---------------
Code           Visual Studio Code.app  visual-studio-code  95          SAFE_TO_ADOPT
Docker         Docker.app              docker-desktop      100         ALREADY_BREW
WireGuard      WireGuard.app           -                   100         LEAVE_APP_STORE
OneDrive       OneDrive.app            -                   0           MANUAL_REVIEW
```

Example command preview:

```text
Safe-to-adopt candidates — commands are printed only, not executed:
  brew install --cask --adopt visual-studio-code    # Code
```

## Algorithm

Priority order:

1. Discover `.app` bundles in configured application directories.
2. Read app metadata from `Contents/Info.plist`.
3. Detect App Store installation via Spotlight metadata and `_MASReceipt`.
4. Read installed Homebrew casks.
5. Build cask candidates using a conservative bundle-id alias database and name heuristics.
6. Verify the cask artifact using `brew info --json=v2 --cask <candidate>`.
7. Compute confidence and recommendation.
8. Print or export report.

## Validation

Run local verification:

```bash
pytest
ruff check .
python -m compileall brew_adoption_audit scripts
brew-adoption-audit --format table
```

Expected result:

- tests pass
- Ruff passes
- Python sources compile
- CLI prints a report
- the final line says `No system changes were made.`

## Exit behavior

If Homebrew is not available in `PATH`, the CLI prints an error and exits with code `2`.

If the audit succeeds, the CLI exits with code `0`.

## Known limitations

- `SAFE_TO_ADOPT` means “safe candidate”, not “guaranteed operation”. Homebrew definitions, app self-updaters, and local state can change.
- Some vendor-managed or package-based applications may remain `MANUAL_REVIEW` even when a cask candidate exists, because there is no directly verifiable `.app` artifact match.
- If Homebrew API metadata is unavailable, some non-installed casks may not be verifiable and may conservatively remain `MANUAL_REVIEW` or `NO_CASK_FOUND`.
- The tool intentionally avoids fuzzy matching and substring matching.

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Compile-check sources:

```bash
python -m compileall brew_adoption_audit scripts
```

## Important note

Review every suggested adoption command before running it manually. This tool does not and should not make adoption decisions irreversible by executing commands for you.
