from multiprocessing import Pool, Manager
from typing import Tuple, List, Optional, Dict, Any

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL
from pm4py.algo.discovery.inductive.fall_through.empty_traces import EmptyTracesUVCL
from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import DecisionGraph
from copy import copy


class POWLEmptyTracesDecisionGraphUVCL(EmptyTracesUVCL):

    @classmethod
    def apply(cls, obj: IMDataStructureUVCL, pool: Pool = None, manager: Manager = None,
              parameters: Optional[Dict[str, Any]] = None) -> Optional[
        Tuple[DecisionGraph, List[IMDataStructureUVCL]]]:
        if cls.holds(obj, parameters):
            data_structure = copy(obj.data_structure)
            del data_structure[()]
            children = [IMDataStructureUVCL(data_structure)]
            dg = DecisionGraph(BinaryRelation(copy(children)), children, children, empty_path=True)
            return dg, children
        else:
            return None
