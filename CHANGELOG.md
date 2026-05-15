# Changelog

## 0.1.1 - 2026-05-16

### Added

### Changed

- Package built web assets into `chatgame/web_static` so installed-mode `chatgame web serve` works after `pip install chatgame`.
- Make `chatgame web setup` validate packaged assets by default, reserving frontend source checks for explicit developer workflows.

### Fixed

- Delay importing the cow-puzzle solver until `chatgame solve` runs so help and web commands still work when image-analysis dependencies are unavailable.
- Make `chatgame web build` fail with a friendly developer-facing error when frontend sources are unavailable instead of raising a raw traceback.
