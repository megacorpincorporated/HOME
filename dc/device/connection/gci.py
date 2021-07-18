"""
This module specifies the Generic Connection Interface superclass.
"""


import abc

from device.models import Device


class GCI(abc.ABCMeta):

    class Message:
        # TODO: figure out generic message interface to be able to properly
        #  address different device capabilities/heartbeats/capability.
        pass

    @abc.abstractmethod
    def discover(cls) -> [Device]:
        """
        Discover devices in the local network that are not yet connected.

        :returns: discovered devices
        """
        pass

    @abc.abstractmethod
    def connect(cls, device: Device) -> bool:
        """
        Connect to the given device.

        :returns: True if connected, else False
        """
        pass

    @abc.abstractmethod
    def send(cls, msg: Message, device: Device) -> bool:
        """
        Sends the parameter message to the given device.

        :returns: True if successful, else False
        """
        pass

    @abc.abstractmethod
    def disconnect(cls, device: Device):
        """
        Disconnects the given device.
        """
        pass

    @abc.abstractmethod
    def notify(cls, callback: callable(Message), device: Device):
        """
        Subscribes to messages from the given device, each message will be
        relayed to the parameter callback.
        """
        pass
