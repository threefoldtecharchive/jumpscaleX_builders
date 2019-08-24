from unittest import TestCase
from loguru import logger
import time


class BaseTest(TestCase):
    LOGGER = logger
    LOGGER.add("builder_{time}.log")

    SMALL_SLEEP = 10
    MEDIUM_SLEEP = 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.info("* Test case : {}".format(self._testMethodName))

    def tearDown(self):
        self.info(" * Tear_down!")

    def info(self, message):
        self.LOGGER.info(message)

    def small_sleep(self):
        time.sleep(self.SMALL_SLEEP)

    def medium_sleep(self):
        time.sleep(self.MEDIUM_SLEEP)
