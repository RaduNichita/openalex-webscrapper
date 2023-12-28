import requests

from config.config import Config

cfg = Config.instance()

def initialize_config():
    print(Config.get_base_url())

def main():
    initialize_config()

if __name__ == "__main__":
    main()