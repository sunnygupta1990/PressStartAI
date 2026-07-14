"""
Application entry point.
"""

from src.core.config import Config
from src.core.logger import setup_logger
from src.core.pipeline import Pipeline


class Application:

    def __init__(self):

        self.config = Config()

        self.logger = setup_logger()

        self.pipeline = Pipeline()

    def run(self):

        self.logger.info("PressStartAI Started")

        self.pipeline.run()