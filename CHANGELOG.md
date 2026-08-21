# Changelog

## 0.1.12 - 2026-08-21

### Added

- Add `chatgame --tree-brief`, which renders the same registered command surface as `--tree` without parameter signatures.
- Add full/brief tree contract tests and installed-console-script CI readbacks.

### Changed

- Replace the package-local Click tree renderer with ChatStyle `add_tree_option()` and require `chatstyle>=0.2.0,<0.3.0`.
- Make the public `chatgame` root name explicit and describe leaf outputs and side effects in the registered tree.
- Remove the unused ChatEnv runtime dependency because ChatGame has no env/profile/config behavior.
- Bound Click and MkDocs Material to the supported compatibility ranges.

## 0.1.11 - 2026-08-12

### Fixed

- Fix the tag-triggered publish workflow guard so it fetches the default branch without re-fetching tags, avoiding annotated-tag checkout conflicts before the PyPI upload step.
- Align the Trusted Publishing workflow with the active PyPI publisher row that accepts any GitHub environment for `ChatArch/ChatGame` + `publish.yml`.

### Notes

- Carries forward the `0.1.10` CLI tree and MkDocs release content; `v0.1.10` failed before upload and was not published to PyPI.

## 0.1.10 - 2026-08-12

### Added

- Add `chatgame --tree`, generated from the real registered Click command surface.
- Add bilingual CLI tree documentation and expose `--tree` in README/docs quick command examples.

### Changed

- Align MkDocs to the ChatArch public docs domain with `mkdocs-static-i18n` and Material emoji rendering.
- Harden the tag-driven PyPI publish workflow with tag/version/default-branch/PyPI duplicate guards.
- Use the package `__version__` for source-mode `chatgame --version`, so `PYTHONPATH=src` CLI smoke works before installation.

### Fixed

- Remove stale scaffold `chatgame hello` examples from README surfaces.

## 0.1.8 - 2026-05-24

### Added

- Add Vitest component coverage and Playwright browser E2E coverage for the Web UI core paths.
- Add CI verification that rebuilt `src/chatgame/web_static` is committed when frontend sources change.
- Document the frontend testing workflow and expand CI/package/install-smoke gates for packaged Web assets.

### Changed

- Build packaged Web static assets before package/install-smoke checks so wheel validation matches the published artifact.

## 0.1.7 - 2026-05-16

### Fixed

- Fix 10x10 board detection for cropped screenshots where the top of the board appears above the previous fixed skip threshold.
- Add regression coverage for the 32660 10x10 screenshot pair so cropped and full screenshots parse to the same color matrix.

## 0.1.6 - 2026-05-16

### Added

- Package gameplay docs under `chatgame/docs` so installed-mode Web UI can read rules and strategy content.

### Changed

- Make `chatgame web serve` and the docs API read gameplay markdown from package resources in both editable and wheel installs.

### Fixed

- Restore `玩法说明` and `攻略` content after `pip install .` / `pip install -e .` by shipping the markdown files with the Python package.
- Add an API regression test that checks packaged gameplay docs are returned from `/api/games/cow-puzzle/docs`.

## 0.1.5 - 2026-05-16

### Added

- Add a dedicated `🎉` completion panel for solved gameplay boards.

### Changed

- Make `演示解` replay the solution in click order instead of filling the whole board at once.
- Simplify gameplay feedback so rule hints trigger after clicks instead of on hover.

### Fixed

- Split gameplay exclusion feedback into four stable visual categories: same row, same column, same region, and adjacent.
- Remove hover-driven motion and pulsing conflict animation so the board no longer jitters while the cursor moves.

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
