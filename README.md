# brew-adoption-audit

`brew-adoption-audit` is a read-only macOS audit tool that compares installed `.app` bundles with Homebrew casks and produces a conservative adoption plan.

It is designed for developers and administrators who want to know which manually installed macOS applications are good candidates for:

```bash
brew install --cask --adopt <cask>
```

The tool **does not execute adoption**. It only prints or exports a report.

## Safety contract

This tool is audit-only.

It **will not**:

- install software
- uninstall software
- adopt software
- update Homebrew
- upgrade Homebrew packages
- run `brew cleanup`
- modify `/Applications`
- modify `~/Applications`
- modify `~/Library`
- move, copy, or delete application bundles

The only optional write operation is report export via `--output`.

The generated adoption commands are command previews only.

## Requirements

- macOS
- Python 3.14+
- Homebrew installed and available in `PATH`

## Installation for local development

```bash
git clone https://github.com/pospanet/brew-adoption-audit.git
cd brew-adoption-audit
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

Default table output:

```bash
brew-adoption-audit
```

Audit both system and user Applications folders:

```bash
brew-adoption-audit --include-user-applications
```

Export JSON:

```bash
brew-adoption-audit --format json --output report.json
```

Export Markdown:

```bash
brew-adoption-audit --format markdown --output report.md
```

Verbose mode shows read-only commands:

```bash
brew-adoption-audit --verbose
```

## Recommendations

The tool emits one of these recommendations:

| Recommendation | Meaning |
|---|---|
| `LEAVE_APP_STORE` | Application appears to be installed from the Mac App Store. Keep App Store as update source. |
| `ALREADY_BREW` | Application is already managed by a Homebrew cask. |
| `SAFE_TO_ADOPT` | A Homebrew cask was found and its `.app` artifact matches the installed app bundle. |
| `MANUAL_REVIEW` | Possible cask exists, but the tool cannot safely prove adoption suitability. |
| `NO_CASK_FOUND` | No credible Homebrew cask candidate was found. |

## Algorithm

Priority order:

1. Read app metadata from `Info.plist`.
2. Detect App Store installation via Spotlight metadata and `_MASReceipt`.
3. Read installed Homebrew casks.
4. Build cask candidates using a conservative bundle-id alias database and name heuristics.
5. Verify the cask artifact using `brew info --json=v2 --cask <candidate>`.
6. Compute confidence and recommendation.
7. Print or export report.

## Important note

`SAFE_TO_ADOPT` still means “safe candidate”, not “guaranteed operation”. Homebrew, cask definitions, application self-updaters, and local app state can change. Review the report before running any adoption commands manually.
