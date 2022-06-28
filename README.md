## UClip - Clipboard image uploader

Command line utility to upload a clipboard image to a
configurable B2 bucket, returning the image URL.

### Demo



> After upload, the displayed URL is also copied to the clipboard.


### Install via pip or [pipx](https://github.com/pypa/pipx)
```shell
pipx install uclip
```




### The OS Keychain Service is used for secure API credential storage:

| Windows                | MacOS         | Ubuntu LTS 20.04    |
|------------------------|---------------|---------------------|
| [Credential locker][1] | [Keychain][2] | [Secret Service][3] |




[1]: https://docs.microsoft.com/en-us/windows/uwp/security/credential-locker
[2]: https://developer.apple.com/documentation/security/certificate_key_and_trust_services/keys/storing_keys_in_the_keychain
[3]: https://specifications.freedesktop.org/secret-service/latest/