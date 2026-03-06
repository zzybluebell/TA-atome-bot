This folder is reserved for distributable macOS build artifacts.

Local outputs such as `AtomeDesk-macOS.zip` are intentionally ignored from git because:
- the file size is too large for normal repository storage
- generated packages may embed local runtime secrets if not sanitized

Keep release binaries in GitHub Releases or another artifact storage instead of git history.
