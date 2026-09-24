from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from common.ui import run_demo
run_demo(Path(__file__).with_name('demo.py'), 'database_health', 'AI Database Health Assistant')
