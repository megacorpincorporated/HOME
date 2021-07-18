import logging

import hume_storage as storage

from device.models import Device


LOGGER = logging.getLogger(__name__)


def model_init():
    """
    Initialize models.
    """
    LOGGER.info("model-init")
    storage.register(Device)


def pre_start():
    """
    Pre-start, before starting applications.
    """
    LOGGER.info("pre-start")


def start():
    """
    Starts up the device application.
    """
    LOGGER.info("device start")


def stop():
    """
    Stop the HTTP listener.
    """
    LOGGER.info("device stop")
