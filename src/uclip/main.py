from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypeVar, Any, NoReturn

import click
import pyperclip
from rich.console import Console
from rich.progress import Progress
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from PIL import Image, ImageGrab
from typing import ParamSpec
from yaspin import yaspin
from yaspin.core import Yaspin

from uclip import __version__
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


def attempt(
    func: Callable[[P], T], *args: Any, sp: Yaspin, verbose: bool = False
) -> T | NoReturn:
    try:
        return func(*args)
    except Exception as e:
        sp.hide()
        if verbose:
            console.print_exception()
        else:
            console.print(f"❌ [yellow]{e}")
        raise SystemExit(1)


def assert_exists(target: T, msg: str, sp: Yaspin) -> T | NoReturn:
    if not target:
        sp.hide()
        console.print(f"❌ [yellow]{msg}")
        raise SystemExit(1)
    return target


def humanize_url(url: str) -> str:
    # noinspection HttpUrlsUsage
    return url.replace("https://", "").replace("http://", "")


def run() -> None:
    """
    Main function
    """
    sp: Yaspin
    with yaspin(text="Loading config...", color="green") as sp:
        config = Config()
        result = attempt(config.load, sp=sp)

        if not result:
            sp.fail("❌ Config not found. Please run `uclip --config`.")
            return

        if not config.valid:
            sp.fail("❌ Config not valid. Please run `uclip --config`.")
            return

        sp.text = "Loading image from clipboard..."
        img = ImageGrab.grabclipboard()
        assert_exists(img, "No image found in clipboard", sp)

        sp.text = "Connecting to B2..."
        uploader = attempt(Uploader, config, sp=sp)

        # Check the image type
        ext = Image.MIME.get(img.format).split("/")[1]

        with NamedTemporaryFile(suffix=f".{ext}") as f:
            img.save(f.name)
            sp.hide()
            with RichProgressListener("Uploading...", transient=True) as pbar:
                url_result = attempt(uploader.upload, f.name, pbar, sp=sp)

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        console.print(f"✅ {url_result}")


def run_file(file_path: str) -> None:
    # Prompt to provide file name
    use_rand = inquirer.confirm(
        message="Generate random file name? Otherwise use name from path.",
        mandatory=True,
    ).execute()

    sp: Yaspin
    with yaspin(text="Loading config...", color="green") as sp:
        config = Config()
        result = attempt(config.load, sp=sp)

        if not result:
            sp.fail("❌ Config not found. Please run `uclip --config`.")
            return

        if not config.valid:
            sp.fail("❌ Config not valid. Please run `uclip --config`.")
            return

        file = Path(file_path).resolve()
        f_name = file.stem if not use_rand else None
        assert_exists(file.is_file, "File not found.", sp)

        sp.text = "Connecting to B2..."
        uploader = attempt(Uploader, config, sp=sp)

        sp.hide()
        with RichProgressListener("Uploading...", transient=True) as pbar:
            url_result = attempt(uploader.upload, str(file), f_name, pbar, sp=sp)

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        console.print(f"✅ {url_result}")


def run_del(file_name: str) -> None:
    # Initialize the config
    with yaspin(text="Loading config...", color="green") as sp:
        config = Config()
        result = attempt(config.load, sp=sp)

        assert_exists(result, "Config not found. Please run `uclip --config`.", sp)
        assert_exists(
            config.valid, "Config not valid. Please run `uclip --config`.", sp
        )

        sp.text = "Connecting to B2..."
        uploader = attempt(Uploader, config, sp=sp)

        sp.text = "Deleting file..."
        file = attempt(uploader.find_file, file_name, sp=sp)
        assert_exists(file, "File not found", sp)
        attempt(uploader.delete_file, file, sp=sp)
        sp.hide()

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
@click.option("--config", "-c", is_flag=True, help="Configure uclip")
@click.option("--version", "-v", is_flag=True, help="Show uclip version")
@click.option("--delete", "-d", required=False, help="Delete a file")
def uclip(file, config, version, delete):
    if config:
        config_setup()
    elif file:
        run_file(file)
    elif version:
        console.print(f"uclip [blue]v{__version__}")
    elif delete:
        run_del(delete)
    else:
        run()
