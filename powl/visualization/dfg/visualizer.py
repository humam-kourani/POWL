from copy import deepcopy
from enum import Enum

import graphviz
from pm4py.objects.dfg.obj import DFG
from pm4py.util import exec_utils
from pm4py.visualization.common import gview, save as gsave

from powl.visualization.dfg.variants import base


class Variants(Enum):
    BASE = base


DEFAULT_VARIANT = Variants.BASE


def apply(dfg: DFG, variant=DEFAULT_VARIANT) -> graphviz.Digraph:
    """
    Visualize a frequency/performance directly-follows graph

    Parameters
    -----------------
    dfg
        Directly-follows graph

    Returns
    -----------------
    gviz
        Graphviz digraph
    """
    dfg_obj = deepcopy(dfg)
    return exec_utils.get_variant(variant).apply(dfg_obj)


def save(gviz, output_file_path, parameters=None):
    """
    Save the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    output_file_path
        Path where the GraphViz output should be saved
    """
    gsave.save(gviz, output_file_path, parameters=parameters)
    return ""


def view(gviz, parameters=None):
    """
    View the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    """
    return gview.view(gviz, parameters=parameters)


def matplotlib_view(gviz, parameters=None):
    """
    Views the diagram using Matplotlib

    Parameters
    ---------------
    gviz
        Graphviz
    """

    return gview.matplotlib_view(gviz, parameters=parameters)
