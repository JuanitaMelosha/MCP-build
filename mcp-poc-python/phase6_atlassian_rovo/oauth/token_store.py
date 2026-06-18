from __future__ import annotations

import json
import os
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from cryptography.fernet import Fernet


@dataclass
class OAuthToken:
    """Atlassian OAuth access and refresh token data."""

    access_token: str
    refresh_token: str | None
    expires_at: float
    scope: str
    token_type: str = "Bearer"

    def is_expired(self, leeway_seconds: int = 60) -> bool:
        """Return True when the access token is expired or nearly expired."""
        return time.time() >= self.expires_at - leeway_seconds


class TokenStore:
    """Encrypted local token storage for the learning lab."""

    def __init__(
        self,
        token_path: Path = Path(".tokens.json"),
        key_path: Path = Path(".token_key"),
    ) -> None:
        self.token_path = token_path
        self.key_path = key_path
        self._fernet = Fernet(self._load_or_create_key())

    def save(self, token: OAuthToken) -> None:
        """Encrypt and save the Atlassian token."""
        encrypted = self._fernet.encrypt(json.dumps(asdict(token)).encode()).decode()
        self.token_path.write_text(json.dumps({"atlassian": encrypted}, indent=2))
        os.chmod(self.token_path, stat.S_IRUSR | stat.S_IWUSR)

    def load(self) -> OAuthToken | None:
        """Load and decrypt the Atlassian token."""
        if not self.token_path.exists():
            return None
        records = json.loads(self.token_path.read_text())
        encrypted = records.get("atlassian")
        if encrypted is None:
            return None
        data = json.loads(self._fernet.decrypt(encrypted.encode()).decode())
        return OAuthToken(**data)

    def delete(self) -> None:
        """Delete the stored token file."""
        if self.token_path.exists():
            self.token_path.unlink()

    def _load_or_create_key(self) -> bytes:
        """Load or create an owner-only encryption key."""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        os.chmod(self.key_path, stat.S_IRUSR | stat.S_IWUSR)
        return key

