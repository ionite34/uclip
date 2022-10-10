from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypeVar, Any, NoReturn

import click
import pyperclip
from rich.console import Console
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from PIL import Image, ImageGrab
from typing import ParamSpec
from yaspin import yaspin
from yaspin.core import Yaspin

from uclip import __version__
from uclip.compat import cached_property
from uclip.config import Config
from uclip.uploader import Uploader
from uclip.progress import RichProgressListener

_instr_alt_url = (
    "Optional Alternate URL that will be copied, this should "
    "have a CNAME record to the root of the B2 bucket"
)
_instr_b2_img_path = "Leave blank for root"
_instr_random_chars = "Length of the random file name (Recommended between 4-12)"

P = ParamSpec("P")
T = TypeVar("T")

console = Console()
options = {"verbose": False}


def humanize_url(url: str) -> str:
    """Removes the protocol from a URL."""
    # noinspection HttpUrlsUsage
    return url.replace("https://", "").replace("http://", "")


class App:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.sp: Yaspin | None = None

    def spin(self, *args, **kwargs) -> Yaspin:
        self.sp = yaspin(*args, **kwargs)
        return self.sp

    @contextmanager
    def sp_text(self, text: str) -> None:
        # Check if a spinner is defined
        if self.sp is None:
            # If not, create one
            self.sp = yaspin(text=text, color="green")
        self.sp.text = text
        yield None
        self.sp.text = ""

    def attempt(self, func: Callable[[P], T], *args: Any) -> T:
        """
        Attempt to run a function, if it fails, print the error and exit

        Args:
            func: The function to run
            args: The arguments to pass to the function
            sp: The spinner to use
            verbose: Whether to print the error message

        Returns:
            The result of the function
        """
        try:
            return func(*args)
        except Exception as e:
            self.sp.hide()
            if self.verbose:
                console.print_exception()
            else:
                console.print(f"❌ [yellow]{e}")
            raise SystemExit(1)

    def assert_exists(self, *target: T, msg: str) -> T:
        if not all(target):
            self.sp.hide()
            console.print(f"❌ [yellow]{msg}")
            raise SystemExit(1)
        return target

    @cached_property
    def config(self) -> Config:
        """Loads configs."""
        with self.sp_text("Loading config..."):
            config = Config()
            result = self.attempt(config.load)
            self.assert_exists(
                result,
                config.valid,
                msg="Config not found. Please run `uclip --config`.",
            )
        return config

    @cached_property
    def uploader(self) -> Uploader:
        config = self.config
        with self.sp_text("Connecting to B2..."):
            return self.attempt(Uploader, config)

    def run(self) -> None:
        """Main image upload routine."""
        with self.sp_text("Loading image from clipboard..."):
            img = ImageGrab.grabclipboard()
            img_ext = Image.MIME.get(img.format).split("/")[1]
            self.assert_exists(img, msg="No image found in clipboard")

        uploader = self.uploader

        with NamedTemporaryFile(mode="wb", suffix=f".{img_ext}") as f:
            img.save(f)
            self.sp.hide()
            with RichProgressListener("Uploading...", transient=True) as pbar:
                url_result = self.attempt(uploader.upload, f.name, None, pbar)

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        console.print(f"✅ {url_result}")

    def run_file(self, file_path: str) -> None:
        # Prompt to provide file name
        use_rand = inquirer.confirm(
            message="Generate random file name? Otherwise use name from path.",
            mandatory=True,
        ).execute()

        file = Path(file_path).resolve()
        f_name = file.stem if not use_rand else None
        self.assert_exists(file.is_file, msg="File not found.")

        uploader = self.uploader

        self.sp.hide()
        with RichProgressListener("Uploading...", transient=True) as pbar:
            url_result = self.attempt(uploader.upload, str(file), f_name, pbar)

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        console.print(f"✅ {url_result}")

    def run_del(self, file_name: str) -> None:
        # Initialize the config
        uploader = self.uploader

        with self.sp_text("Deleting file..."):
            file = self.attempt(uploader.find_file, file_name)
            self.assert_exists(file, msg="File not found")
            self.attempt(uploader.delete_file, file)

        self.sp.hide()
        console.print(f"🗑️  Deleted [blue]{file_name}")


def config_setup():
    config = Config()
    config["b2_api_id"] = inquirer.text("B2 Application ID:", mandatory=True).execute()
    config["b2_api_key"] = inquirer.secret(
        "B2 Application Key:", mandatory=True
    ).execute()
    config["b2_bucket_name"] = inquirer.text(
        "B2 Bucket Name:", mandatory=True
    ).execute()
    config["b2_img_path"] = (
            inquirer.text(
                "B2 Upload Path in Bucket:", long_instruction=_instr_b2_img_path
            ).execute()
            or ""
    )
    config["alt_url"] = (
            inquirer.text("Alternate URL:", long_instruction=_instr_alt_url).execute() or ""
    )
    config["random_chars"] = int(
        inquirer.text(
            "File Name Length:",
            mandatory=True,
            long_instruction=_instr_random_chars,
            validate=NumberValidator(float_allowed=False),
        ).execute()
    )
    config.save()


@click.command()
@click.option("--file", "-f", help="Upload a file from path")
@click.option("--delete", "-d", required=False, help="Delete a file")
@click.option("--config", "-c", is_flag=True, help="Configure uclip")
@click.option("--version", "-v", is_flag=True, help="Show uclip version")
@click.option("--verbose", "-vv", is_flag=True, help="Run with verbose tracing")
def uclip(file: str, delete: str, config: bool, version: bool, verbose: bool):
    if version:
        console.print(f"uclip v{__version__}")
        raise SystemExit(0)

    if config:
        config_setup()
        raise SystemExit(0)

    app = App(verbose=verbose)

    if file:
        app.run_file(file)
    elif delete:
        app.run_del(delete)
    else:
        app.run()
