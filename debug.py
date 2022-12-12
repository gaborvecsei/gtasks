import sys
from pathlib import Path
from gt import gt_cli

sys.path.append(str(Path.cwd()))
gt_cli.main()

