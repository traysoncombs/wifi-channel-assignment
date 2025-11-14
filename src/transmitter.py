import abc
import enum
from typing import Tuple, List

from src.path_loss import AbstractPathLossModel, Position

"""
Class that houses channels with a fixed width
"""


class Channels:
    def __init__(self, base_freq: float, num_channels: int, channel_width: float, base_freq_distance: float):
        self.channels = []
        self.base_freq = base_freq
        self.num_channels = num_channels
        self.channel_width = channel_width

        for i in range(1, num_channels+1):
            self.channels.append(base_freq + base_freq_distance * (i-1))

    def get_channel_base(self, index: int) -> float:
        """
        Returns the base frequency of the channel in MHz
        """

        return self.channels[index - 1]

    def get_channel_center(self, index: int) -> float:
        """
        Returns the center frequency of the channel in MHz
        """
        return self.channels[index - 1] + (self.channel_width / 2)

    def is_overlapping(self, channel_1: int, channel_2: int) -> bool:
        channel_1_base = self.get_channel_base(channel_1)
        channel_2_base = self.get_channel_base(channel_2)
        first_channel = min(channel_1_base, channel_2_base)
        second_channel = max(channel_1_base, channel_2_base)
        return second_channel - first_channel <= self.channel_width

    def channel_centers(self) -> List[float]:
        return [self.get_channel_center(ch) for ch in self.channels]


class Transmitter:
    def __init__(self, channel: int, tx_power: float, position: Position, channels: Channels,
                 path_loss: AbstractPathLossModel, sir_power_ref: float):
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
        self.path_loss = path_loss
        self.sir_power_ref = sir_power_ref

    def get_received_power(self, position: Position) -> float:
        return self.path_loss.received_power_at_position(self.tx_power, self.position, position,
                                                         self.channels.get_channel_center(self.channel))

    def get_signal_interference_ratio(self, other_transmitter) -> float:
        """
        Returns the normalized signal interference between two transmitters if they are operating on overlapping channels.
        :param other_transmitter:
        :return:
        """
        if not self.channels.is_overlapping(self.channel, other_transmitter.channel):
            return 2**32

        normal_pos = self.path_loss.position_from_received_power(self.tx_power, self.sir_power_ref, self.position,
                                                                 other_transmitter.position,
                                                                 self.channels.get_channel_center(self.channel))
        rx_power_at_norm_pos = other_transmitter.get_received_power(normal_pos)

        return (10**(self.sir_power_ref/10)) / (10**(rx_power_at_norm_pos/10))

    def __str__(self) -> str:
        return f"{self.position}, {self.channel}"

    def __repr__(self) -> str:
        return f"router_{self.position}_{id(self)}"