from multiprocessing import Pool, Manager
from typing import List, TypeVar, Tuple, Optional, Dict, Any, Type

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure, IMDataStructureUVCL, IMDataStructureDFG
from pm4py.algo.discovery.inductive.fall_through.abc import FallThrough
from powl.discovery.total_order_based.inductive.fall_through.activity_concurrent import POWLActivityConcurrentUVCL
from powl.discovery.total_order_based.inductive.fall_through.activity_once_per_trace import POWLActivityOncePerTraceUVCL
from powl.discovery.total_order_based.inductive.fall_through.flower import POWLFlowerModelUVCL, POWLFlowerModelDFG
from powl.discovery.total_order_based.inductive.fall_through.strict_tau_loop import POWLStrictTauLoopUVCL
from powl.discovery.total_order_based.inductive.fall_through.tau_loop import POWLTauLoopUVCL
from powl.objects.obj import POWL

T = TypeVar('T', bound=IMDataStructure)
S = TypeVar('S', bound=FallThrough)


class FallThroughFactory:

    @classmethod
    def get_fall_throughs(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> List[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [POWLActivityOncePerTraceUVCL, POWLActivityConcurrentUVCL,
                    POWLStrictTauLoopUVCL, POWLTauLoopUVCL, POWLFlowerModelUVCL]
        elif type(obj) is IMDataStructureDFG:
            return [POWLFlowerModelDFG]
        return list()

    @classmethod
    def fall_through(cls, obj: T, pool: Pool, manager: Manager, parameters: Optional[Dict[str, Any]] = None) -> Optional[Tuple[POWL, List[T]]]:
        for f in FallThroughFactory.get_fall_throughs(obj):
            r = f.apply(obj, pool, manager, parameters)
            if r is not None:
                return r
        return None
