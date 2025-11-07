import abc
import enum
from typing import Tuple

from src.path_loss import AbstractPathLossModel

"""
Class that houses channels with a fixed width
"""
class Channels:
    def __init__(self, base_freq: float, num_channels: int, channel_width: float):
        self.channels = []
        self.base_freq = base_freq
        self.num_channels = num_channels
        self.channel_width = channel_width

        for i in range(num_channels):
            self.channels[i] = base_freq + channel_width * i

    def get_channel_base(self, index: int) -> float:
        """
        Returns the base frequency of the channel in MHz
        """

        return self.channels[index]

    def get_channel_center(self, index: int) -> float:
        """
        Returns the center frequency of the channel in MHz
        """
        return self.channels[index] + (self.channel_width / 2)


class Transmitter:
    def __init__(self, channel: int, tx_power: int, position: Tuple[int, int], channels: Channels,
                 path_loss: AbstractPathLossModel):
        """
        Initializes the transmitter
        :param channel: Channel index, should be contained within channels
        :param tx_power: Power of the transmitter in DBm
        :param position: Relative position of the transmitter in (x, y)
        :param channels: Possible channel values
        :param path_loss: The path loss model of the transmitter
        """
        self.channel = channel
        self.tx_power = tx_power
        self.position = position
        self.channels = channels
