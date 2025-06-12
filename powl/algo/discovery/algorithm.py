from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL
from pm4py import util
from pm4py.algo.discovery.inductive.algorithm import Parameters
from pm4py.util import xes_constants as xes_util
from pm4py.util.compression import util as comut
from pm4py.util.compression.dtypes import UVCL
from pm4py.util import exec_utils
from pm4py.objects.log.obj import EventLog

from powl.objects.obj import POWL
from powl.algo.discovery.inductive.variants.im_decision_graph_clustering import POWLInductiveMinerDecisionGraphClustering
from powl.algo.discovery.inductive.variants.im_decision_graph_maximal import \
    POWLInductiveMinerDecisionGraphMaximal
from powl.algo.discovery.inductive.variants.im_dynamic_clustering_frequencies import \
    POWLInductiveMinerDynamicClusteringFrequency
from powl.algo.discovery.inductive.variants.im_tree import IMBasePOWL
from powl.algo.discovery.inductive.variants.im_brute_force import POWLInductiveMinerBruteForce
from powl.algo.discovery.inductive.variants.im_maximal import POWLInductiveMinerMaximalOrder
from powl.algo.discovery.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant

from typing import Optional, Dict, Any, Union, Type
import pandas as pd


def get_variant(variant: POWLDiscoveryVariant) -> Type[IMBasePOWL]:
    if variant == POWLDiscoveryVariant.TREE:
        return IMBasePOWL
    elif variant == POWLDiscoveryVariant.BRUTE_FORCE:
        return POWLInductiveMinerBruteForce
    elif variant == POWLDiscoveryVariant.MAXIMAL:
        return POWLInductiveMinerMaximalOrder
    elif variant == POWLDiscoveryVariant.DYNAMIC_CLUSTERING:
        return POWLInductiveMinerDynamicClusteringFrequency
    elif variant == POWLDiscoveryVariant.DECISION_GRAPH_MAX:
        return POWLInductiveMinerDecisionGraphMaximal
    elif variant == POWLDiscoveryVariant.DECISION_GRAPH_CLUSTERING:
        return POWLInductiveMinerDecisionGraphClustering
    else:
        raise Exception('Invalid Variant!')


def apply(obj: Union[EventLog, pd.DataFrame, UVCL], parameters: Optional[Dict[Any, Any]] = None,
          variant=POWLDiscoveryVariant.MAXIMAL) -> POWL:
    if parameters is None:
        parameters = {}
    ack = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_util.DEFAULT_NAME_KEY)
    tk = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters, xes_util.DEFAULT_TIMESTAMP_KEY)
    cidk = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, util.constants.CASE_CONCEPT_NAME)
    if type(obj) in [EventLog, pd.DataFrame]:
        uvcl = comut.get_variants(comut.project_univariate(obj, key=ack, df_glue=cidk, df_sorting_criterion_key=tk))
    else:
        uvcl = obj

    algorithm = get_variant(variant)
    im = algorithm(parameters)
    res = im.apply(IMDataStructureUVCL(uvcl), parameters)
    res = res.simplify()

    return res
