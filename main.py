import logging

from utils.utils import *

logging.basicConfig(level=logging.INFO)
logging.info("Setting LOGLEVEL to INFO")

if __name__ == "__main__":
    print(os.environ.get('TASK_SLOT', ''))
    app.run(host="0.0.0.0", port=5000)
