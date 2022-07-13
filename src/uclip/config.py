from __future__ import annotations

import base64
import json

import keyring

_required_values = {
    "b2_api_id",
    "b2_api_key",
    "b2_bucket_name",
    "b2_img_path",
    "alt_url",
    "random_chars",
}


class Config(dict):
    def __init__(self):
        """Stores persistent user settings in keyring."""
        super().__init__()

    def load(self) -> bool:
        """Load config from keyring."""
        # Get the keyring entry
        try:
            data = keyring.get_password("uclip", "config")
        except keyring.core.backend.errors.KeyringError as e:
            raise RuntimeError(f"Error Accessing Keychain: {e}")
        if not data:
            return False
        # Decode the base64 data
        data = base64.b64decode(data.encode("ascii"))
        # Load the json data
        data = json.loads(data.decode("utf-8"))
        # Load the data into self
        self.update(data)
        return True

    def save(self):
        """Save the current config to keyring."""
        data = json.dumps(self).encode("utf-8")
        data = base64.b64encode(data).decode("ascii")
        keyring.set_password("uclip", "config", data)

    @property
    def valid(self) -> bool:
        """Checks if the config is valid for use."""
        return all(key in self for key in _required_values)
