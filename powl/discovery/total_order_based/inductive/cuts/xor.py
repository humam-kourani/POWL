from abc import ABC
from typing import Any, Dict, Generic, Optional

from pm4py.algo.discovery.inductive.cuts.xor import (
    ExclusiveChoiceCut,
    ExclusiveChoiceCutDFG,
    ExclusiveChoiceCutUVCL,
    T,
)
from pm4py.algo.discovery.inductive.dtypes.im_ds import (
    IMDataStructureDFG,
    IMDataStructureUVCL,
)
from pm4py.objects.process_tree.obj import Operator

from powl.objects.obj import OperatorPOWL


class POWLExclusiveChoiceCut(ExclusiveChoiceCut, ABC, Generic[T]):
    @classmethod
    def operator(cls, parameters: Optional[Dict[str, Any]] = None) -> OperatorPOWL:
        return OperatorPOWL(Operator.XOR, [])


class POWLExclusiveChoiceCutUVCL(
    ExclusiveChoiceCutUVCL, POWLExclusiveChoiceCut[IMDataStructureUVCL], ABC
):
    pass


class POWLExclusiveChoiceCutDFG(
    ExclusiveChoiceCutDFG, POWLExclusiveChoiceCut[IMDataStructureDFG], ABC
):
    pass
