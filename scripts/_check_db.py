import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
try:
    import database
    print("import ok")
except Exception as e:
    print(type(e).__name__, e)
    raise
