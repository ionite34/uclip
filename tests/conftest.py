import pytest
from keyring.backend import KeyringBackend


class MockKeyring(KeyringBackend):

    """A test keyring which is just an in-memory dictionary."""

    priority = 1
    _store = {}

    def set_password(self, servicename, username, password) -> None:
        self._store.setdefault(servicename, {})[username] = password

    def get_password(self, servicename, username):
        return self._store.get(servicename, {}).get(username)

    def delete_password(self, servicename, username):
        self._store.setdefault(servicename, {}).pop(username, None)


# Fixture that builds a test keyring and returns it.
@pytest.fixture(scope="function")
def mem_keyring():
    import keyring as kr
    kr.set_keyring(MockKeyring())
    return kr
