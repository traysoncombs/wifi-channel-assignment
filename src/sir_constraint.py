from typing import Dict, Callable, Tuple, List, Union

from constraint import Problem, MinConflictsSolver

from src.transmitter import Transmitter, Channels


def sir_constraint_creator(tx_dict: Dict[str, Transmitter], minimum_sir: float) -> Callable:
    """
    This functions creates a constraint function that ensures the signal-interference ratio (SIR) between two given transmitters
    is at least `minimum_sir`.
    :param tx_dict: A dictionary that contains all the transmitters with the key being a unique name for each.
                    the variables passed to constraint solver should be the same as the keys for this dict.
    :param minimum_sir: The minimum SIR between two transmitters.
    :return: A function that takes two tuples (tx name, channel assignment) and computes the SIR between them for the given
             channel assignments.
    """

    def sir_constraint(tx1_channel: Tuple[str, int], tx2_channel: Tuple[str, int]) -> bool:
        tx1 = tx_dict[tx1_channel[0]]
        tx2 = tx_dict[tx2_channel[0]]

        tx1.channel = tx1_channel[1]
        tx2.channel = tx2_channel[1]
        sir = tx1.get_signal_interference_ratio(tx2)

        return sir > minimum_sir

    return sir_constraint


def cumulative_sir_constraint_creator(tx_dict: Dict[str, Transmitter], minimum_avg_sir: float, minimum_pair_sir: float) -> Callable:
    """
    This functions creates a constraint function that ensures the average SIR between all transmitters is > minimum_sir.
    :param minimum_pair_sir: The minimum pairwise SIR between two transmitters.
    :param tx_dict: A dictionary that contains all the transmitters with the key being a unique name for each.
                    the variables passed to constraint solver should be the same as the keys for this dict.
    :param minimum_avg_sir: The minimum average SIR between all transmitters.
    :return: A function that takes two tuples (tx name, channel assignment) and computes the SIR between them for the given
             channel assignments.
    """

    def sir_constraint(tx1_channel: Tuple[str, int], *args) -> bool:
        sir = 0
        tx1 = tx_dict[tx1_channel[0]]
        for tx2_channel in args:
            tx2 = tx_dict[tx2_channel[0]]

            tx1.channel = tx1_channel[1]
            tx2.channel = tx2_channel[1]

            tmp_sir = tx1.get_signal_interference_ratio(tx2)
            if tmp_sir < minimum_pair_sir:
                return False
            sir += tmp_sir

        return (sir / (len(args))) >= minimum_avg_sir

    return sir_constraint

def create_and_solve_constraint_problem(transmitters: List[Transmitter], channels: Channels, min_sir: float, average: bool, min_avg_sir: float = 0.95, max_steps: int = 1000) -> \
        Union[List[Transmitter], None]:
    """
    This functions creates a constraint problem for the given transmitters and channel setup.
    :param min_avg_sir: The minimum average SIR between all transmitters to be used if `average` is true
    :param average: Set to true to use the average SIR between all transmitters instead of minimum SIR between pairs.
    :param transmitters: A list of all transmitters.
    :param channels: An object representing the possible channels and their frequencies.
    :param min_sir: The minimum SIR between two transmitters.
    :return: A solution to the problem if it exists.
    """
    tx_dict = {tx.__repr__(): tx for tx in transmitters}
    tx_names = list(tx_dict.keys())
    channels = range(1, channels.num_channels + 1)

    problem = Problem()

    # Create a variable for each transmitter whose possible values are in a list of tuples of the following form:
    # (transmitter name, channel)
    for tx_name in tx_dict.keys():
        problem.addVariable(tx_name, [(tx_name, ch) for ch in channels])

    if average:
        constraint = cumulative_sir_constraint_creator(tx_dict, min_avg_sir, min_sir)
        for i in range(len(tx_names)):
            every_other = []
            for j in range(0, len(tx_names)):
                if i != j:
                    every_other.append((tx_names[j]))
            problem.addConstraint(constraint, [tx_names[i], *every_other])
    else:
        constraint = sir_constraint_creator(tx_dict, min_sir)
        # Create a SIR constraint for each possible grouping of two routers.
        for i in range(len(tx_names) - 1):
            for j in range(i + 1, len(tx_names)):
                problem.addConstraint(constraint, [tx_names[i], tx_names[j]])



    problem.setSolver(MinConflictsSolver(steps=max_steps))
    solution = problem.getSolution()
    if solution is None:
        return None

    # Apply the solution to our transmitters and return a list of them.
    for tx_name in tx_dict.keys():
        tx_dict[tx_name].channel = solution[tx_name][1]

    return list(tx_dict.values())
