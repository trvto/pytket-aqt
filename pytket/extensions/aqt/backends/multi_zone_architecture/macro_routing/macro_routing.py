import heapq
from copy import deepcopy
from dataclasses import dataclass
import networkx as nx

from ..macro_architechture_graph import MultiZoneMacroArch
from ..optypes_multizone_arch import MultiZoneOperation


@dataclass
class Zone:
    id: int
    qubit_sets: list[set[int]]
    max_n_qubits: int

    def unused_capacity(self) -> int:
        return self.max_n_qubits - sum(
            [len(qubit_set) for qubit_set in self.qubit_sets]
        )


@dataclass
class ZonesList:
    zones: list[Zone]
    qubit_to_zone_map: dict[int, tuple[int, int]]
    max_qubits_total: int

    def __init__(self, macro_arch: MultiZoneMacroArch):
        self.max_qubits_total = macro_arch.max_qubits
        zone_data_dict = nx.get_node_attributes(macro_arch, "zone_data")
        zones: list[Zone] = []
        for zone in macro_arch.zones:
            zone_data = zone_data_dict[zone]
            new_zone = Zone(
                id=zone,
                qubit_sets=list(),
                max_n_qubits=zone_data.zone_config.max_zone_occupancy,
            )
            zones.append(new_zone)

        zones.sort(key=lambda zone_from_list: zone_from_list.max_n_qubits)
        self.zones = zones
        self.qubit_to_zone_map = {}

    def unused_capacity(self) -> int:
        return self.max_qubits_total - len(self.qubit_to_zone_map)

    def _try_add_qubit(self, qubit: int) -> bool:
        """Add a single qubit that is not currently mapped to a zone

        Because this qubit has no links interaction with others yet, don't add based on priority,
         just fill up smallest zones (last in list) first
        """
        for index, zone in reversed(list(enumerate(self.zones))):
            if zone.unused_capacity() > 0:
                zone.qubit_sets.append({qubit})
                self.qubit_to_zone_map[qubit] = (index, len(zone.qubit_sets) - 1)
                return True
        return False

    def _try_add_qubit_pair(self, qubit_0: int, qubit_1) -> bool:
        for index, zone in enumerate(self.zones):
            if zone.unused_capacity() > 1:
                zone.qubit_sets.append({qubit_0, qubit_1})
                self.qubit_to_zone_map[qubit_0] = (index, len(zone.qubit_sets) - 1)
                return True
        return False

    def _try_add_qubit_to_qubit_set(
        self, qubit: int, zone_index: int, set_index: int
    ) -> bool:
        """Don't try to move sets around for now"""
        zone = self.zones[zone_index]
        if zone.unused_capacity() > 0:
            zone.qubit_sets[set_index].add(qubit)
            self.qubit_to_zone_map[qubit] = (zone_index, set_index)
            return True
        return False

    def _merge_distinct_sets(
        self,
        target_zone_index: int,
        target_index: int,
        source_zone_index: int,
        source_index: int,
    ) -> None:
        target_zone_set = self.zones[target_zone_index].qubit_sets[target_index]
        source_zone_set = self.zones[source_zone_index].qubit_sets[source_index]
        target_zone_set.update(source_zone_set)
        for qubit in source_zone_set:
            self.qubit_to_zone_map[qubit] = (target_zone_index, target_index)
        source_zone_set.clear()

    def _try_merge_qubit_sets(
        self, zone_index_0: int, set_index_0: int, zone_index_1: int, set_index_1: int
    ) -> bool:
        if zone_index_0 == zone_index_1:
            if set_index_0 == set_index_1:
                return True
            self._merge_distinct_sets(
                zone_index_0, set_index_0, zone_index_1, set_index_1
            )
            return True
        zone_0 = self.zones[zone_index_0]
        zone_1 = self.zones[zone_index_1]
        if zone_0.unused_capacity() > len(zone_1.qubit_sets[set_index_1]):
            self._merge_distinct_sets(
                zone_index_0, set_index_0, zone_index_1, set_index_1
            )
            return True
        if zone_1.unused_capacity() > len(zone_0.qubit_sets[set_index_0]):
            self._merge_distinct_sets(
                zone_index_1, set_index_1, zone_index_0, set_index_0
            )
            return True
        return False

    def try_accommodate_operation(self, operation: MultiZoneOperation) -> bool:
        if operation.n_qubits == 1:
            if operation.qubits[0] in self.qubit_to_zone_map.keys():
                return True
            return self._try_add_qubit(operation.qubits[0])
        if operation.n_qubits == 2:
            qubit_0 = operation.qubits[0]
            qubit_1 = operation.qubits[1]
            match (
                self.qubit_to_zone_map.get(qubit_0),
                self.qubit_to_zone_map.get(qubit_1),
            ):
                case (None, None):
                    return self._try_add_qubit_pair(qubit_0, qubit_1)
                case ((zone_index, set_index), None):
                    return self._try_add_qubit_to_qubit_set(
                        qubit_1, zone_index, set_index
                    )
                case (None, (zone_index, set_index)):
                    return self._try_add_qubit_to_qubit_set(
                        qubit_0, zone_index, set_index
                    )
                case ((zone_index_0, set_index_0), (zone_index_1, set_index_1)):
                    return self._try_merge_qubit_sets(
                        zone_index_0, set_index_0, zone_index_1, set_index_1
                    )
        return False


def macro_routing(
    operations: list[MultiZoneOperation], macro_arch: MultiZoneMacroArch
) -> list[MultiZoneOperation]:
    zones_list = ZonesList(macro_arch)
    zones_list_2 = deepcopy(zones_list)
    frontier_index = 0
    for i, operation in enumerate(operations):
        if not zones_list.try_accommodate_operation(operation):
            frontier_index = i
    frontier_index_2 = 0
    for i, operation in enumerate(operations[frontier_index:]):
        if not zones_list_2.try_accommodate_operation(operation):
            frontier_index_2 = i


def route_across_frontier(
    zone_list_0: ZonesList,
    zone_list_1: ZonesList,
    operations: list[MultiZoneOperation],
    macro_arch: MultiZoneMacroArch,
):
    qubits_0 = {qubit for qubit in zone_list_0.qubit_to_zone_map.keys()}
    qubits_1 = {qubit for qubit in zone_list_1.qubit_to_zone_map.keys()}
    for qubit_1 in qubits_1:
        if qubit_1 in qubits_0:
            zone_index_0, set_index_0 = zone_list_0.qubit_to_zone_map[qubit_1]
            zone0 = zone_list_0.zones[zone_index_0]
            zone_index_1, set_index_1 = zone_list_1.qubit_to_zone_map[qubit_1]
            zone1 = zone_list_1.zones[zone_index_1]
            shortest_path = macro_arch.shortest_paths[zone0.id][zone1.id]
