# Changelog

## 0.1.4 - 2026-05-16

### Added

- Add `--host` to `chatgame web serve` so Web UI can bind to `0.0.0.0` for LAN/IP access.

### Changed

- Reduce the user-facing `chatgame web` surface to installed-mode commands: `setup` and `serve`.
- Keep `chatgame web setup` focused on installed-mode runtime checks instead of frontend development dependencies.
- Document `chatgame web serve --host 0.0.0.0` for IP-based Web access.

## 0.1.3 - 2026-05-16

### Added

- Add a playable Web cow-puzzle game with 6x6, 8x8, and 10x10 size selection.
- Add a verified unique-solution level pool for gameplay and solver examples.
- Add hover/click influence highlighting for row, column, adjacent, and same-region effects.
- Add generation and uniqueness validation documentation for cow-puzzle levels.

### Changed

- Make gameplay restart randomly refresh within the current fixed-size verified pool.
- Make solver examples clickable so users can directly run the solve flow without manual upload.

### Fixed

- Reject non-unique screenshots in the solve API instead of returning an arbitrary solution.
- Keep Web serving from eagerly importing solver/parser dependencies.

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
