from abc import ABC
from typing import Any, Optional, Dict, Generic

from pm4py.algo.discovery.inductive.cuts.concurrency import ConcurrencyCut, ConcurrencyCutUVCL, T
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL
from powl.objects.obj import StrictPartialOrder


class POWLConcurrencyCut(ConcurrencyCut, ABC, Generic[T]):

    @classmethod
    def operator(cls, parameters: Optional[Dict[str, Any]] = None) -> StrictPartialOrder:
        return StrictPartialOrder([])


class POWLConcurrencyCutUVCL(ConcurrencyCutUVCL, POWLConcurrencyCut[IMDataStructureUVCL]):
    pass

