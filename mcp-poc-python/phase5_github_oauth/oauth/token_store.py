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
    """Stored OAuth token data."""

    access_token: str
    token_type: str = "bearer"
    scope: str = ""
    refresh_token: str | None = None
    expires_at: float | None = None

    def is_expired(self, leeway_seconds: int = 60) -> bool:
        """Return True when the access token is expired or nearly expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at - leeway_seconds


class TokenStore:
    """Encrypted local token storage for a single learning-lab user."""

    def __init__(
        self,
        token_path: Path = Path(".tokens.json"),
        key_path: Path = Path(".token_key"),
    ) -> None:
        self.token_path = token_path
        self.key_path = key_path
        self._fernet = Fernet(self._load_or_create_key())

    def save(self, provider: str, token: OAuthToken) -> None:
        """Encrypt and save a token for one provider."""
        tokens = self._load_all()
        plaintext = json.dumps(asdict(token)).encode()
        tokens[provider] = self._fernet.encrypt(plaintext).decode()
        self._write_all(tokens)

    def load(self, provider: str) -> OAuthToken | None:
        """Load and decrypt a token for one provider."""
        encrypted = self._load_all().get(provider)
        if encrypted is None:
            return None
        data = json.loads(self._fernet.decrypt(encrypted.encode()).decode())
        return OAuthToken(**data)

    def delete(self, provider: str) -> None:
        """Delete a stored provider token."""
        tokens = self._load_all()
        tokens.pop(provider, None)
        self._write_all(tokens)

    def _load_or_create_key(self) -> bytes:
        """Load the encryption key or create one with owner-only permissions."""
        if self.key_path.exists():
            return self.key_path.read_bytes()

        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        os.chmod(self.key_path, stat.S_IRUSR | stat.S_IWUSR)
        return key

    def _load_all(self) -> dict[str, str]:
        """Load encrypted token records."""
        if not self.token_path.exists():
            return {}
        return json.loads(self.token_path.read_text())

    def _write_all(self, tokens: dict[str, str]) -> None:
        """Write encrypted token records with owner-only permissions."""
        self.token_path.write_text(json.dumps(tokens, indent=2))
        os.chmod(self.token_path, stat.S_IRUSR | stat.S_IWUSR)

