# Algorithm

1. Discover `.app` bundles in configured application directories.
2. Parse each app's `Contents/Info.plist`.
3. Detect App Store origin through Spotlight metadata and `_MASReceipt`.
4. Read Homebrew installed casks.
5. Read Homebrew available casks.
6. Build candidate casks from:
   - curated bundle-id aliases,
   - normalized app names,
   - normalized `.app` bundle names.
7. For each candidate, inspect `brew info --json=v2 --cask`.
8. Verify whether the cask declares the same `.app` artifact.
9. Emit recommendation and confidence score.
