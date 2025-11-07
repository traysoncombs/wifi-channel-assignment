import abc
from typing import List, Dict


class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

"""
Base class for creating a path loss model
"""
class AbstractPathLossModel(abc.ABC):
    @abc.abstractmethod
    def path_loss_between_positions(self, tx_power: float, tx_pos: Position, rx_pos: Position) -> float:
        """
        Return the path loss between the two positions
        :param tx_power: Transmitter power in dbm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The path loss between the two positions in dbm
        """
        pass



"""
An implementation of the partitioned path loss model.
"""
class PartitionedPathLossModel(AbstractPathLossModel):
    def __init__(self, ref_path_loss: float, exponent_positions: Dict[Position, float]):
        self.ref_path_loss = ref_path_loss
        self.exponent_positions = exponent_positions
        pass

    def path_loss_between_positions(self, tx_power: float, tx_pos: Position, rx_pos: Position):
        pass

