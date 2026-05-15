from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

ASSETS = ROOT / "assets" / "img"
IMG_8x8  = ASSETS / "cow_puzzle_test2.png"   # 8×8，与 Level 24 同关
IMG_10x10 = ASSETS / "cow_puzzle_test.png"    # 10×10
