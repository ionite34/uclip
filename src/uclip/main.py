from PIL import ImageGrab, Image
import click
from yaspin import yaspin as spinner
import pyperclip
from tempfile import NamedTemporaryFile
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator

from .config import Config
from .uploader import Uploader

_instr_alt_url = ('Optional Alternate URL that will be copied, this should '
                  'have a CNAME record to the root of the B2 bucket')
_instr_b2_img_path = 'Leave blank for root'
_instr_random_chars = 'Length of the random file name (Recommended between 4-12)'


def run() -> None:
    """
    Main function
    """
    # Initialize the config
    with spinner(text='Loading config...', color='green') as sp:
        config = Config()
        try:
            result = config.load()
        except RuntimeError as e:
            sp.text = ''
            sp.fail(f'❌ {e}')
            return

        if not result:
            sp.fail('❌ Config not found. Please run `uclip --config`.')
            return

        if not config.valid:
            sp.fail('❌ Config not valid. Please run `uclip --config`.')
            return

        # Get image from clipboard
        sp.text = 'Getting image from clipboard...'
        img = ImageGrab.grabclipboard()
        if not img:
            sp.fail('❌ [No image found]')
            return

        # Connect to B2
        sp.text = 'Connecting to B2...'
        try:
            uploader = Uploader(config)
        except RuntimeError as e:
            sp.fail('❌')
            print(e)
            return

        # Check the image type
        ext = Image.MIME.get(img.format).split('/')[1]

        # Save the image to a temporary file
        with NamedTemporaryFile(suffix=f'.{ext}') as f:
            img.save(f.name)
            sp.text = 'Uploading image...'
            try:
                url_result = uploader.upload(f.name)
            except RuntimeError as e:
                sp.fail(f'❌')
                print(e)
                return

        # Copy the URL to the clipboard
        pyperclip.copy(url_result)

        # Print the URL
        sp.text = url_result
        sp.ok('✅')


def run_del(file_name: str) -> None:
    # Initialize the config
    with spinner(text='Loading config...', color='green') as sp:
        config = Config()
        try:
            result = config.load()
        except RuntimeError as e:
            sp.text = ''
            sp.fail(f'❌ {e}')
            return

        if not result:
            sp.fail('❌ Config not found. Please run `uclip --config`.')
            return

        if not config.valid:
            sp.fail('❌ Config not valid. Please run `uclip --config`.')
            return

        # Connect to B2
        sp.text = 'Connecting to B2...'
        try:
            uploader = Uploader(config)
        except RuntimeError as e:
            sp.fail('❌')
            print(e)
            return

        # Delete the file
        sp.text = 'Deleting file...'
        try:
            # Find file
            file = uploader.find_file(file_name)
            if not file:
                sp.text = 'File not found'
                sp.fail('❌')
                return
            # Delete file
            uploader.delete_file(file)
        except RuntimeError as e:
            sp.text = e
            sp.fail('❌')
            return

        # Print the URL
        sp.text = f'Deleted {file_name}'
        sp.ok('🗑️')


def config_setup():
    config = Config()
    config['b2_api_id'] = inquirer.text('B2 Application ID:', mandatory=True).execute()
    config['b2_api_key'] = inquirer.secret('B2 Application Key:', mandatory=True).execute()
    config['b2_bucket_name'] = inquirer.text('B2 Bucket Name:', mandatory=True).execute()
    config['b2_img_path'] = inquirer.text('B2 Upload Path in Bucket:',
                                          long_instruction=_instr_b2_img_path).execute() or ''
    config['alt_url'] = inquirer.text('Alternate URL:', long_instruction=_instr_alt_url).execute() or ''
    config['random_chars'] = int(inquirer.text('File Name Length:', mandatory=True,
                                               long_instruction=_instr_random_chars,
                                               validate=NumberValidator(float_allowed=False)).execute())
    config.save()


@click.command()
@click.option('--config', '-c', is_flag=True, help='Configure uclip')
@click.option('--delete', '-d', required=False, help='Delete a file')
def uclip(config, delete):
    if config:
        config_setup()
    elif delete:
        run_del(delete)
    else:
        run()
