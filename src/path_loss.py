import abc
import math
from math import sqrt, log10


class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, position) -> float:
        return sqrt((self.x - position.x) ** 2 + (self.y - position.y) ** 2)

    def mag(self):
        return sqrt(self.x ** 2 + self.y ** 2)

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f})"

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


"""
Base class for creating a path loss model
"""
class AbstractPathLossModel(abc.ABC):
    @abc.abstractmethod
    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position, frequency: float,
                                   spectral_loss: float):
        """
        Return the path loss [DBm] between the two positions
        :param frequency: The center frequency of the signal in MHz
        :param tx_power: Transmitter power in dbm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The path loss between the two positions in dbm
        """
        pass

    @abc.abstractmethod
    def position_from_received_power(self, tx_power: float, rx_power: float, tx_pos: Position, rx_pos: Position,
                                     frequency: float) -> float:
        pass


class FreeSpacePathLossModel(AbstractPathLossModel):
    def __init__(self, pl_exp):
        self.pl_exp = pl_exp

    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position, frequency: float,
                                   spectral_loss: float):
        """
        Computes received power at a position.
        :param frequency: The center frequency of the signal in MHz
        :param tx_power: transmission power in DBm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The received power at rx_pos from tx_pos
        """
        # Find the path between the two routers and compute the distance.
        path = Position((rx_pos.x - tx_pos.x), (rx_pos.y - tx_pos.y))
        distance = path.mag()

        wavelength = (3 * 10 ** 8) / (frequency * 10 ** 6)
        path_loss = 10 * self.pl_exp * log10((4 * math.pi * distance) / wavelength)

        # Compute the received power assuming unity gain
        return tx_power - path_loss - spectral_loss

    def position_from_received_power(self, tx_power: float, rx_power: float, tx_pos: Position, rx_pos: Position,
                                     frequency: float) -> Position:
        """
        Finds the distance from `tx_pos` at which the received power is equal to `rx_power`
        and returns a position at said distance from the transmitter in the direction of `rx_power`.
        :param tx_power: The transmission power.
        :param rx_power: The received power
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver (Used for determining the direction)
        :param frequency: The center frequency of the signal in MHz.
        :return: Positon in meters.
        """
        # Compute the path along which our signal might travel.
        path = Position((rx_pos.x - tx_pos.x), (rx_pos.y - tx_pos.y))
        path_mag = path.mag()

        wavelength = (3 * 10 ** 8) / (frequency * 10 ** 6)
        rx_power_linear = 10 ** (rx_power / 10)
        tx_power_linear = 10 ** (tx_power / 10)

        # Compute distance using FSPL with our exponent
        distance = wavelength / (4 * math.pi * ((rx_power_linear / tx_power_linear) ** (1 / self.pl_exp)))

        # Find the position by adding a vector x, such that |x| = distance, to our transmitters position.
        scale_factor = distance / path_mag
        return Position(tx_pos.x + path.x * scale_factor, tx_pos.y + path.y * scale_factor)