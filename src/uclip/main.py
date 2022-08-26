from __future__ import annotations

from collections.abc import Callable
from tempfile import NamedTemporaryFile
from typing import TypeVar, Any, NoReturn

import click
import pyperclip
from rich.console import Console
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from PIL import Image, ImageGrab
from typing_extensions import ParamSpec
from yaspin import yaspin as spinner

from .config import Config
from .uploader import Uploader

_instr_alt_url = (
    "Optional Alternate URL that will be copied, this should "
    "have a CNAME record to the root of the B2 bucket"
)
_instr_b2_img_path = "Leave blank for root"
_instr_random_chars = "Length of the random file name (Recommended between 4-12)"

P = ParamSpec('P')
T = TypeVar('T')

console = Console()


def attempt(func: Callable[[P], T], *args: Any, sp: spinner, verbose: bool = False) -> T | NoReturn:
    try:
        return func(*args)
    except Exception as e:
        sp.fail("❌")
        if verbose:
            console.print_exception()
        else:
            console.print(f"|- {e}")
        raise SystemExit(1) from e


def assert_exists(target: T, msg: str, sp: spinner) -> T | NoReturn:
    if not target:
        sp.fail("❌")
        console.print(f"|- {msg}")
        raise SystemExit(1)
    return target


def run() -> None:
    """
    Main function
    """
    with spinner(text="Loading config...", color="green") as sp:
        config = Config()
        result = attempt(config.load, sp=sp)

        if not result:
            sp.fail("❌ Config not found. Please run `uclip --config`.")
            return

        if not config.valid:
            sp.fail("❌ Config not valid. Please run `uclip --config`.")
            return

        sp.text = "Getting image from clipboard..."
        img = ImageGrab.grabclipboard()
        assert_exists(img, "No image found in clipboard", sp)

        sp.text = "Connecting to B2..."
        uploader = attempt(Uploader, config, sp=sp)

        # Check the image type
        ext = Image.MIME.get(img.format).split("/")[1]

        with NamedTemporaryFile(suffix=f".{ext}") as f:
            img.save(f.name)
            sp.text = "Uploading image..."
            url_result = attempt(uploader.upload, f.name, sp=sp)

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        # Print the URL
        sp.text = url_result
        sp.ok("✅")


def run_del(file_name: str) -> None:
    # Initialize the config
    with spinner(text="Loading config...", color="green") as sp:
        config = Config()
        result = attempt(config.load, sp=sp)

        assert_exists(result, "Config not found. Please run `uclip --config`.", sp)
        assert_exists(config.valid, "Config not valid. Please run `uclip --config`.", sp)

        sp.text = "Connecting to B2..."
        uploader = attempt(Uploader, config, sp=sp)

        sp.text = "Deleting file..."
        file = attempt(uploader.find_file, file_name, sp=sp)
        assert_exists(file, "File not found", sp)
        attempt(uploader.delete_file, file, sp=sp)

        sp.text = f"Deleted {file_name}"
        sp.ok("🗑️")


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
            ).execute() or ""
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
@click.option("--config", "-c", is_flag=True, help="Configure uclip")
@click.option("--delete", "-d", required=False, help="Delete a file")
def uclip(config, delete):
    if config:
        config_setup()
    elif delete:
        run_del(delete)
    else:
        run()
