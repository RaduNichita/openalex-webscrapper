import logging

from config.config import Config

from prometheus_flask_exporter import PrometheusMetrics

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.utils import *

metrics = PrometheusMetrics(app)
cfg = Config.instance()


limiter = Limiter(get_remote_address, app=app, default_limits=[
                  "20000 per day", "3000 per hour, 30 per minute"])

logging.basicConfig(level=logging.INFO)
logging.info("Setting LOGLEVEL to INFO")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
