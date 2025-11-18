from enum import Enum
from typing import Any, Dict, Optional

from pm4py.objects.ocel.obj import OCEL
from pm4py.util import exec_utils

from powl.discovery.object_centric.variants.flattening import miner as flatten_miner
from powl.discovery.object_centric.variants.oc_powl import miner as oc_powl_miner


class Variants(Enum):
    FLATTENING = flatten_miner
    OC_POWL = oc_powl_miner


def apply(
    ocel: OCEL,
    variant=Variants.FLATTENING,
    parameters: Optional[Dict[Any, Any]] = None,
) -> Dict[str, Any]:
    """
    Discovers an object-centric Petri net from the provided object-centric event log.

    Parameters
    -----------------
    ocel
        Object-centric event log
    variant
        Variant of the algorithm to be used
    parameters
        Variant-specific parameters

    Returns
    ----------------
    ocpn
        Object-centric Petri net model, as a dictionary of properties.
    """
    return exec_utils.get_variant(variant).apply(ocel, parameters=parameters)
