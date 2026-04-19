"""
Re-encrypt all stored client credentials under the current primary key.

Usage — rotation procedure:
  1. Generate a new key:
       python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  2. Prepend it to ENCRYPTION_KEYS in .env (newest first), keeping the old key:
       ENCRYPTION_KEYS=<NEW_KEY>,<OLD_KEY>
  3. Restart the backend (uvicorn --reload does NOT pick up .env changes —
     stop and start it manually, or touch any .py file under app/).
  4. Run this script:
       python -m scripts.rotate_credentials
  5. Once it reports success, drop the old key from ENCRYPTION_KEYS and
     restart the backend again.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app import models
from app.security import rotate_credential


def main() -> int:
    db = SessionLocal()
    try:
        clients = db.query(models.Client).filter(
            models.Client.clave_fiscal_encrypted.isnot(None)
        ).all()

        rotated = 0
        failed = []
        for client in clients:
            try:
                client.clave_fiscal_encrypted = rotate_credential(client.clave_fiscal_encrypted)
                rotated += 1
            except Exception as e:
                failed.append((client.id, client.name, str(e)))

        if failed:
            db.rollback()
            print(f"ABORTED: {len(failed)} client(s) failed to rotate:")
            for cid, name, err in failed:
                print(f"  - client {cid} ({name}): {err}")
            return 1

        db.commit()
        print(f"OK: rotated {rotated} credential(s).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
