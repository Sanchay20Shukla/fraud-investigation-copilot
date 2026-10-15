"""Community Cloud entry point: full synthetic demo without a separate API server."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent/'dashboard'/'app.py'),
               init_globals={'CLOUD_DEMO': True})
