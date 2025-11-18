import importlib
import tempfile
from enum import Enum
from typing import Any, Dict, Optional

import graphviz
from graphviz import Digraph
from pm4py.objects.bpmn.obj import BPMN

from pm4py.util import constants, exec_utils
from pm4py.visualization.common import gview, save as gsave


SPLIT_LABELS = False


class Parameters(Enum):
    FORMAT = "format"
    RANKDIR = "rankdir"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"


def get_label(name):
    parts = name.split(" ")
    if SPLIT_LABELS and len(parts) >= 3:
        return " ".join(parts[:2]) + "\n" + " ".join(parts[2:])
    else:
        return name


def apply(
    bpmn_graph: BPMN, parameters: Optional[Dict[Any, Any]] = None
) -> graphviz.Digraph:
    """
    Visualize a BPMN graph

    Parameters
    -------------
    bpmn_graph
        BPMN graph
    parameters
        Parameters of the visualization, including:
         - Parameters.FORMAT: the format of the visualization
         - Parameters.RANKDIR: the direction of the representation (default: LR)

    Returns
    ------------
    gviz
        Graphviz representation
    """
    if parameters is None:
        parameters = {}

    from pm4py.objects.bpmn.obj import BPMN
    from pm4py.objects.bpmn.util.sorting import get_sorted_nodes_edges

    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    rankdir = exec_utils.get_param_value(
        Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ
    )
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 28)
    font_size = str(font_size)
    bgcolor = exec_utils.get_param_value(
        Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR
    )

    filename = tempfile.NamedTemporaryFile(suffix=".gv")
    filename.close()

    viz = Digraph(
        "", filename=filename.name, engine="dot", graph_attr={"bgcolor": bgcolor}
    )
    viz.graph_attr["rankdir"] = rankdir
    # viz.attr(nodesep='1')
    # viz.attr(ranksep='0.4')

    nodes, edges = get_sorted_nodes_edges(bpmn_graph)

    for n in nodes:
        n_id = str(id(n))
        if isinstance(n, BPMN.Task):
            viz.node(
                n_id, shape="box", label=get_label(n.get_name()), fontsize=font_size
            )
        elif isinstance(n, BPMN.StartEvent):
            viz.node(
                n_id,
                label="",
                shape="circle",
                fontsize=font_size,
                width="0.6",
                height="0.6",
            )
        elif isinstance(n, BPMN.EndEvent):
            viz.node(
                n_id,
                label="",
                shape="circle",
                fontsize=font_size,
                penwidth="3.0",
                width="0.6",
                height="0.6",
            )
        elif isinstance(n, BPMN.ParallelGateway):
            with importlib.resources.path(
                "powl.visualization.powl.variants.icons", "gate_and.svg"
            ) as gimg:
                xor_image = str(gimg)
                viz.node(
                    n_id,
                    label="",
                    shape="diamond",
                    width="0.8",
                    height="0.8",
                    fixedsize="true",
                    image=xor_image,
                )
            # viz.node(n_id, label="+", shape="diamond", fontsize=font_size)
        elif isinstance(n, BPMN.ExclusiveGateway):
            with importlib.resources.path(
                "powl.visualization.powl.variants.icons", "gate.svg"
            ) as gimg:
                xor_image = str(gimg)
                viz.node(
                    n_id,
                    label="",
                    shape="diamond",
                    width="0.8",
                    height="0.8",
                    fixedsize="true",
                    image=xor_image,
                )
            # viz.node(n_id, label="X", shape="diamond", fontsize=font_size)
        elif isinstance(n, BPMN.InclusiveGateway):
            viz.node(n_id, label="O", shape="diamond", fontsize=font_size)
        else:
            viz.node(n_id, label="", shape="circle", fontsize=font_size)

    for e in edges:
        n_id_1 = str(id(e[0]))
        n_id_2 = str(id(e[1]))

        viz.edge(n_id_1, n_id_2, penwidth="2.0")

    viz.attr(overlap="false")

    viz.format = image_format.replace("html", "plain-ext")

    return viz


def save(gviz: graphviz.Digraph, output_file_path: str, parameters=None):
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


def view(gviz: graphviz.Digraph, parameters=None):
    """
    View the diagram

    Parameters
    -----------
    gviz
        GraphViz diagram
    """
    if True:
        return gview.view(gviz, parameters=parameters)


def matplotlib_view(gviz: graphviz.Digraph, parameters=None):
    """
    Views the diagram using Matplotlib

    Parameters
    ---------------
    gviz
        Graphviz
    """
    if True:
        return gview.matplotlib_view(gviz, parameters=parameters)
