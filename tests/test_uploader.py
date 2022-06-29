import pytest

from uclip.config import Config
from uclip.uploader import Uploader, gen_random_name


def test_gen_random_name():
    for i in range(1, 13):
        name = gen_random_name(i)
        assert name.isascii()
        assert len(gen_random_name(i)) == i


def test_uploader():
    cfg = Config()
    cfg['b2_api_id'] = 'test'
    cfg['b2_api_key'] = 'test'
    cfg['b2_bucket_name'] = 'test'
    cfg['b2_img_path'] = 'test'
    with pytest.raises(RuntimeError):
        Uploader(cfg)
