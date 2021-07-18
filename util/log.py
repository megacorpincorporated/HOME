import logging
import logging.handlers


HANDLER_STREAM = "s"


def set_up_logger_for(app_tag, name, log_level, handler_type):
    """
    Generic log setup function.

    :param app_tag: application tag to mark log output
    :param name: logger name
    :type log_level: logging.DEBUG for example
    :param handler_type: string for which handler type should be created
    """
    formatter = logging.Formatter(fmt=f"{{asctime}} {{levelname:^8}} "
                                      f"{app_tag} {{name}} - {{message}}",
                                  style="{",
                                  datefmt="%d/%m/%Y %H:%M:%S")

    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(log_level)

    if handler_type == HANDLER_STREAM:
        handler = logging.StreamHandler()  # Print logging messages
    # elif ...

    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    logger.addHandler(handler)
