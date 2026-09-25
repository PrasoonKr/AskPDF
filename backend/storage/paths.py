from pathlib import Path

import hashlib

def get_user_storage_dir(user_email: str) -> Path:
    # Use a safe hash for the directory name to avoid invalid characters from emails
    safe_dir = hashlib.md5(user_email.encode()).hexdigest()
    storage_dir = Path(f"backend/storage/{safe_dir}")
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir