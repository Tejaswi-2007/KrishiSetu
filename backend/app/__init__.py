import sys
import os

# Add repository root and the 'backend' directory to PYTHONPATH so that imports like
# `from app.core....` resolve to the package located at `backend/app`.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (repo_root, backend_dir):
    if p not in sys.path:
        sys.path.insert(0, p)


