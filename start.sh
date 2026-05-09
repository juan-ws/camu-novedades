#!/bin/bash
# Run seed if the database is empty, then start the server
python3 seed.py
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
