import yaml
import logging, logging.config
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

LOG_CONFIG_PATH = "config/logger.yml"
TEST_MODEL_PATH = "model/"

def logger_config():
    with open(LOG_CONFIG_PATH, "r") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))
    return logging.getLogger(__name__)
