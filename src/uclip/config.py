from __future__ import annotations

import base64
import json

import keyring

_required_values = {
    'b2_api_id',
    'b2_api_key',
    'b2_bucket_name',
    'b2_img_path',
    'alt_url',
    'random_chars'
}


# Config Class for storing persistent user settings
class Config(dict):
    def __init__(self):
        super().__init__()

    def load(self) -> bool:
        # Get the keyring entry
        try:
            data = keyring.get_password('uclip', 'config')
        except keyring.core.backend.errors.KeyringError as e:
            raise RuntimeError(f'Error Accessing Keychain: {e}')
        if not data:
            return False
        # Decode the base64 data
        data = base64.b64decode(data.encode('ascii'))
        # Load the json data
        data = json.loads(data.decode('utf-8'))
        # Load the data into self
        self.update(data)
        return True

    def save(self):
        # Get self as json, encode to base64, and store in keyring
        data = json.dumps(self).encode('utf-8')
        data = base64.b64encode(data).decode('ascii')
        keyring.set_password('uclip', 'config', data)

    @property
    def valid(self) -> bool:
        # Checks if the config is valid for use
        return all(key in self for key in _required_values)
