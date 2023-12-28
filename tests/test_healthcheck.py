import pytest
import requests

from config.config import Config

cfg = Config.instance()

def testhealthcheck():
    url = cfg.get_base_url()
    
    response = requests.get(url)
    assert response.status_code == 200


testhealthcheck()
