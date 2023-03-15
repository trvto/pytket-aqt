from abc import ABC, abstractmethod
from dataclasses import dataclass

from .macro_architechture_graph import ZoneId, QubitId


class MultiZoneOperation(ABC):
    @abstractmethod
    @property
    def n_qubits(self) -> int:
        pass

    @abstractmethod
    @property
    def qubits(self) -> list[int]:
        pass


@dataclass
class ShuttleOperation(MultiZoneOperation):

    qubits: set[QubitId]
    start_zone: ZoneId
    target_zone: ZoneId

    @property
    def n_qubits(self) -> int:
        return len(self.qubits)

    @property
    def qubits(self) -> list[int]:
        return [qubit for qubit in self.qubits]


@dataclass
class SwapOperation:
    swap_qubits: tuple[QubitId, QubitId]


@dataclass
class RxOperation(MultiZoneOperation):
    pulse_area: float
    target_qubit: QubitId

    @property
    def n_qubits(self) -> int:
        return 1

    @property
    def qubits(self) -> list[int]:
        return [self.target_qubit]


@dataclass
class RyOperation(MultiZoneOperation):
    pulse_area: float
    target_qubit: QubitId

    @property
    def n_qubits(self) -> int:
        return 1

    @property
    def qubits(self) -> list[int]:
        return [self.target_qubit]


@dataclass
class RzOperation(MultiZoneOperation):
    pulse_area: float
    target_qubit: QubitId

    @property
    def n_qubits(self) -> int:
        return 1

    @property
    def qubits(self) -> list[int]:
        return [self.target_qubit]


@dataclass
class XXPhaseOperation(MultiZoneOperation):
    pulse_area: float
    target_qubits: tuple[QubitId, QubitId]

    @property
    def n_qubits(self) -> int:
        return 2

    @property
    def qubits(self) -> list[int]:
        return [qubit for qubit in self.target_qubits]
