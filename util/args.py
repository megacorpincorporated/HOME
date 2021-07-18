"""
This module is responsible for keeping CLI arguments stored for easy access.
"""


_args: dict


def set_args(**cli_args):
    """
    Assigns input kwargs to internal _args.
    """
    global _args
    _args = cli_args


def get_arg(name):
    """
    Get argument with name.

    :param name: argument to get
    """
    return _args.get(name)  # noqa
