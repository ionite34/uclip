from __future__ import annotations

import os
import random
import string
from urllib.parse import urljoin

import b2sdk.exception as b2_exception
import b2sdk.file_version
from b2sdk.progress import AbstractProgressListener
from b2sdk.v2 import B2Api, InMemoryAccountInfo

from uclip.config import Config


def gen_random_name(length: int) -> str:
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


class Uploader:
    def __init__(self, config: Config):
        """Initializes the uploader."""
        info = InMemoryAccountInfo()
        self.config = config
        self.api = B2Api(info)
        try:
            self.api.authorize_account(
                "production", config["b2_api_id"], config["b2_api_key"]
            )
        except b2_exception.B2Error as e:
            raise RuntimeError(f"Could not connect to B2: {e}")
        self.bucket = self.api.get_bucket_by_name(config["b2_bucket_name"])
        path_in_bucket = config["b2_img_path"]
        if not str(path_in_bucket).endswith("/"):
            self.path_in_bucket = path_in_bucket + "/"
        else:
            self.path_in_bucket = path_in_bucket

    def find_file(self, file_name: str) -> b2sdk.file_version.DownloadVersion | None:
        """Searches for a file with the given bucket path."""
        b2_path = urljoin(self.path_in_bucket, file_name)
        # Try to download
        try:
            search = self.bucket.get_file_info_by_name(b2_path)
        except b2_exception.FileNotPresent:
            return None
        return search

    def upload(
        self,
        file_path: str,
        upload_name: str | None = None,
        progress_listener: AbstractProgressListener | None = None,
    ):
        """Uploads a file to the B2 bucket."""
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)

        # Shorten the .jpg extension
        if ext == ".jpeg":
            ext = ".jpg"

        # Generate a random name, check if exists up to 5 times
        if upload_name:
            if self.find_file(upload_name):
                raise RuntimeError(f"File {upload_name} already exists")
        else:
            for i in range(5):
                upload_name = gen_random_name(self.config["random_chars"]) + ext
                if i >= 5:
                    raise RuntimeError(
                        "Could not find a unique name for the file in 5 attempts"
                    )
                if not self.find_file(upload_name):
                    break

        # Upload the file
        b2_path = urljoin(self.path_in_bucket, upload_name)
        try:
            self.bucket.upload_local_file(
                local_file=file_path,
                file_name=b2_path,
                progress_listener=progress_listener,
            )
        except b2_exception.B2Error as e:
            raise RuntimeError(f"Could not upload file: {e}")

        return urljoin(self.config["alt_url"], b2_path)

    @staticmethod
    def delete_file(file_version: b2sdk.file_version.DownloadVersion):
        """Deletes a file from the B2 bucket."""
        try:
            return file_version.delete()
        except b2_exception.B2Error as e:
            raise RuntimeError(f"Failed to delete file: {e}")
