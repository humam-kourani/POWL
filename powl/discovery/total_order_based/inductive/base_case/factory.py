from typing import TypeVar, Optional, Dict, Any, Type, List as TList

from powl.discovery.total_order_based.inductive.base_case.abc import BaseCase
from powl.discovery.total_order_based.inductive.base_case.empty_log import EmptyLogBaseCaseUVCL, EmptyLogBaseCaseDFG
from powl.discovery.total_order_based.inductive.base_case.single_activity import SingleActivityBaseCaseUVCL, \
    SingleActivityBaseCaseDFG
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure, IMDataStructureUVCL, IMDataStructureDFG

from powl.objects.obj import POWL

T = TypeVar('T', bound=IMDataStructure)
S = TypeVar('S', bound=BaseCase)


class BaseCaseFactory:

    @classmethod
    def get_base_cases(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> TList[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [EmptyLogBaseCaseUVCL, SingleActivityBaseCaseUVCL]
        elif type(obj) is IMDataStructureDFG:
            return [EmptyLogBaseCaseDFG, SingleActivityBaseCaseDFG]
        else:
            return []

    @classmethod
    def apply_base_cases(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Optional[POWL]:
        for b in BaseCaseFactory.get_base_cases(obj):
            r = b.apply(obj, parameters)
            if r is not None:
                return r
        return None
