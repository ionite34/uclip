import os
import random
import string
from urllib.parse import urljoin

import b2sdk.exception as b2_exception
from b2sdk.v2 import B2Api, InMemoryAccountInfo, exception

from uclip.config import Config


def gen_random_name(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


class Uploader:
    # Uploads files using the B2 API
    def __init__(self, config: Config):
        info = InMemoryAccountInfo()
        self.config = config
        self.b2_api = B2Api(info)
        try:
            self.b2_api.authorize_account(
                "production", config["b2_api_id"], config["b2_api_key"]
            )
        except b2_exception.B2Error as e:
            raise RuntimeError(f"Could not connect to B2: {e}")
        self.bucket = self.b2_api.get_bucket_by_name(config["b2_bucket_name"])
        path_in_bucket = config["b2_img_path"]
        if not str(path_in_bucket).endswith("/"):
            self.path_in_bucket = path_in_bucket + "/"
        else:
            self.path_in_bucket = path_in_bucket

    def exists(self, file_name: str) -> bool:
        b2_path = f"{self.path_in_bucket}/{file_name}"
        # Try to download
        try:
            search = self.bucket.download_file_by_name(b2_path)
        except b2_exception.FileNotPresent:
            return False
        return not search

    def upload(self, file_path: str):
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)

        # Replace extension
        if ext == ".jpeg":
            ext = ".jpg"

        # Generate a random name
        file_name = gen_random_name(self.config["random_chars"]) + ext

        # Check if the file already exists
        for i in range(5):
            if i >= 5:
                raise RuntimeError(
                    "Could not find a unique name for the file in 5 attempts"
                )
            if self.exists(file_name):
                file_name = gen_random_name(self.config["random_chars"]) + ext
            else:
                break

        # Upload the file
        b2_path = urljoin(self.path_in_bucket, file_name)
        try:
            self.bucket.upload_local_file(file_path, b2_path)
        except exception.B2Error as e:
            raise RuntimeError(f"Could not upload file: {e}")

        return urljoin(self.config["alt_url"], b2_path)
