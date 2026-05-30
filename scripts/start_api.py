"""Start the Evidentia API server with correct PYTHONPATH."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("evidentia.api:app", host="0.0.0.0", port=8000, reload=False)
