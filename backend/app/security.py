from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet, MultiFernet
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))


def _load_encryption_keys() -> List[str]:
    # Single source of truth for fetching encryption keys.
    # To migrate to AWS KMS / GCP Secret Manager / HashiCorp Vault:
    # replace the body of this function with a call to the secrets backend
    # (e.g. boto3 secretsmanager.get_secret_value). The rest of the module
    # does not need to change.
    #
    # ENCRYPTION_KEYS: comma-separated, newest key first. Older keys stay
    # listed so data encrypted with them can still be decrypted until the
    # rotation script has re-encrypted everything.
    # ENCRYPTION_KEY: legacy single-key variable, still honored as fallback.
    multi = os.getenv("ENCRYPTION_KEYS")
    if multi:
        keys = [k.strip() for k in multi.split(",") if k.strip()]
        if keys:
            return keys
    single = os.getenv("ENCRYPTION_KEY")
    if single:
        return [single]
    return [Fernet.generate_key().decode()]


def _build_fernet() -> MultiFernet:
    keys = _load_encryption_keys()
    return MultiFernet([Fernet(k.encode() if isinstance(k, str) else k) for k in keys])


try:
    fernet = _build_fernet()
except Exception:
    fernet = MultiFernet([Fernet(Fernet.generate_key())])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    # rounds=10 is standard for dev/testing (rounds=12 is production default).
    # The cost is embedded in the hash so verify_password always uses the right rounds.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def encrypt_credential(value: str) -> str:
    # Always encrypts with the primary (first) key. Decrypt accepts any key
    # in the MultiFernet chain, so rotation is: prepend a new key, rotate old
    # records with scripts/rotate_credentials.py, then drop the old key.
    return fernet.encrypt(value.encode()).decode()


def decrypt_credential(encrypted_value: str) -> str:
    return fernet.decrypt(encrypted_value.encode()).decode()


def rotate_credential(encrypted_value: str) -> str:
    # Re-encrypt under the current primary key. Used by the rotation script.
    return fernet.rotate(encrypted_value.encode()).decode()
