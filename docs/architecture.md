# Architecture

The project is split into small modules:

- `cli.py` — argument parsing and output routing.
- `audit.py` — orchestration of the audit flow.
- `bundle.py` — `.app` discovery and `Info.plist` parsing.
- `appstore.py` — App Store receipt detection.
- `brew.py` — Homebrew metadata access and cask candidate resolution.
- `artifacts.py` — cask artifact extraction.
- `aliases.py` — conservative bundle-id to cask mapping.
- `recommendation.py` — recommendation decision logic.
- `confidence.py` — confidence scoring.
- `reporting.py` — table, JSON, CSV, Markdown, and HTML output.
- `shell.py` — read-only command runner.
