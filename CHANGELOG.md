# Changelog

## 0.1.2 - 2026-05-16

### Added

### Changed

- Run CI `test` and `install-smoke` on Python 3.10 to match the declared minimum supported version.
- Update quickstart guidance to focus on Python version requirements and clean virtual environments instead of a conda-specific flow.

### Fixed

- Keep installed-mode `chatgame web setup` focused on Web runtime requirements so Python 3.10 users are not blocked by `scikit-learn` / `scipy` ABI issues in optional solver dependencies.

## 0.1.1 - 2026-05-16

### Added

### Changed

- Package built web assets into `chatgame/web_static` so installed-mode `chatgame web serve` works after `pip install chatgame`.
- Make `chatgame web setup` validate packaged assets by default, reserving frontend source checks for explicit developer workflows.

### Fixed

- Delay importing the cow-puzzle solver until `chatgame solve` runs so help and web commands still work when image-analysis dependencies are unavailable.
- Make `chatgame web build` fail with a friendly developer-facing error when frontend sources are unavailable instead of raising a raw traceback.
