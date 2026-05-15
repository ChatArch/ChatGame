# chatgame

**Game puzzle screenshot solver** — take a screenshot, get the solution instantly.

Currently supports: **Cow Puzzle** (color-region constraint · unique row/col · no adjacency — same family as LinkedIn Queens)

---

## Quickstart

```bash
# Install
pip install -e ".[dev]"

# Solve a screenshot (print answer)
chatgame solve level24.png

# Save annotated image
chatgame solve level24.png -o solved.png
```

---

## Features

| Feature | Command |
|---------|---------|
| Solve screenshot, print click order | `chatgame solve <image>` |
| Save annotated image (numbers on grid) | `chatgame solve <image> -o <output>` |
| List supported games | `chatgame games` |
| Check & install dependencies | `chatgame web setup -i` |
| Launch Web UI | `chatgame web serve` |

---

## Local docs preview

```bash
pip install -e ".[docs]"
mkdocs serve
```

Chinese version: [index.md](index.md)
