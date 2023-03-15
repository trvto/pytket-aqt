from dataclasses import dataclass
from typing import NewType

from networkx import Graph, shortest_path  # type: ignore

from .architecture import MultiZoneArchitecture
from .optypes_multizone_arch import MultiZoneOperation

QubitId = NewType("QubitId", int)
ZoneId = NewType("ZoneId", int)


@dataclass(frozen=True)
class MacroZoneConfig:
    max_occupancy: int
    min_occupancy: int


@dataclass()
class MacroZoneData:
    zone_config: MacroZoneConfig


@dataclass(frozen=True)
class MultiZoneMacroArch:
    max_qubits: int
    zones: Graph
    shortest_paths: dict[int, dict[int, list[int]]]


def empty_macro_arch_from_backend(
    architecture: MultiZoneArchitecture,
) -> MultiZoneMacroArch:
    zones = Graph()
    for zone_id, zone in enumerate(architecture.zones):
        zone_type = architecture.zone_types[zone.zone_type_id]
        zone_data = MacroZoneData(
            zone_config=MacroZoneConfig(
                max_occupancy=zone_type.max_ions, min_occupancy=zone_type.min_ions
            ),
        )
        zones.add_node(ZoneId(zone_id), zone_data=zone_data)
    for zone_id, zone in enumerate(architecture.zones):
        for _, connected_zone_id in zone.connected_zones.items():
            zones.add_edge(ZoneId(zone_id), ZoneId(connected_zone_id))
    shortest_paths = shortest_path(zones)
    return MultiZoneMacroArch(
        max_qubits=architecture.n_qubits_max, zones=zones, shortest_paths=shortest_paths
    )
