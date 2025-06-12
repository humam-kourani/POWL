import tempfile
from copy import copy

from graphviz import Digraph

from pm4py.statistics.attributes.log import get as attr_get
from pm4py.objects.dfg.utils import dfg_utils
from pm4py.util import xes_constants as xes
from pm4py.util import exec_utils
from pm4py.statistics.service_time.log import get as serv_time_get
from enum import Enum
from pm4py.util import constants
from typing import Optional, Dict, Any, Tuple
import graphviz
from pm4py.objects.log.obj import EventLog
from collections import Counter


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    FORMAT = "format"
    MAX_NO_EDGES_IN_DIAGRAM = "maxNoOfEdgesInDiagram"
    START_ACTIVITIES = "start_activities"
    END_ACTIVITIES = "end_activities"
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    FONT_SIZE = "font_size"
    RANKDIR = "rankdir"
    BGCOLOR = "bgcolor"


def apply(dfg: Dict[Tuple[str, str], int], log: EventLog = None, parameters: Optional[Dict[Any, Any]] = None, activities_count : Dict[str, int] = None, serv_time: Dict[str, float] = None) -> graphviz.Digraph:
    """
    Visualize a frequency directly-follows graph

    Parameters
    -----------------
    dfg
        Frequency Directly-follows graph
    log
        (if provided) Event log for the calculation of statistics
    activities_count
        (if provided) Dictionary associating to each activity the number of occurrences in the log.
    serv_time
        (if provided) Dictionary associating to each activity the average service time
    parameters
        Variant-specific parameters

    Returns
    -----------------
    gviz
        Graphviz digraph
    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes.DEFAULT_NAME_KEY)
    image_format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    max_no_of_edges_in_diagram = exec_utils.get_param_value(Parameters.MAX_NO_EDGES_IN_DIAGRAM, parameters, 100000)
    start_activities = exec_utils.get_param_value(Parameters.START_ACTIVITIES, parameters, {})
    end_activities = exec_utils.get_param_value(Parameters.END_ACTIVITIES, parameters, {})
    font_size = exec_utils.get_param_value(Parameters.FONT_SIZE, parameters, 32)
    font_size = str(font_size)

    if start_activities is None:
        start_activities = dict()
    if end_activities is None:
        end_activities = dict()
    activities = sorted(list(set(dfg_utils.get_activities_from_dfg(dfg)).union(set(start_activities)).union(set(end_activities))))

    rankdir = exec_utils.get_param_value(Parameters.RANKDIR, parameters, constants.DEFAULT_RANKDIR_GVIZ)
    bgcolor = exec_utils.get_param_value(Parameters.BGCOLOR, parameters, constants.DEFAULT_BGCOLOR)

    if activities_count is None:
        if log is not None:
            activities_count = attr_get.get_attribute_values(log, activity_key, parameters=parameters)
        else:
            # the frequency of an activity in the log is at least the number of occurrences of
            # incoming arcs in the DFG.
            # if the frequency of the start activities nodes is also provided, use also that.
            activities_count = Counter({key: 0 for key in activities})
            for el in dfg:
                activities_count[el[1]] += dfg[el]
            if isinstance(start_activities, dict):
                for act in start_activities:
                    activities_count[act] += start_activities[act]

    if serv_time is None:
        if log is not None:
            serv_time = serv_time_get.apply(log, parameters=parameters)
        else:
            serv_time = {key: 0 for key in activities}

    return graphviz_visualization(activities_count, dfg, image_format=image_format, measure="frequency",
                                           max_no_of_edges_in_diagram=max_no_of_edges_in_diagram,
                                           start_activities=start_activities, end_activities=end_activities, serv_time=serv_time,
                                           font_size=font_size, bgcolor=bgcolor, rankdir=rankdir)


def graphviz_visualization(activities_count, dfg, image_format="png", measure="frequency",
                           max_no_of_edges_in_diagram=100000, start_activities=None, end_activities=None, serv_time=None,
                           font_size="12", bgcolor=constants.DEFAULT_BGCOLOR, rankdir=constants.DEFAULT_RANKDIR_GVIZ):
    """
    Do GraphViz visualization of a DFG graph

    Parameters
    -----------
    activities_count
        Count of attributes in the log (may include attributes that are not in the DFG graph)
    dfg
        DFG graph
    image_format
        GraphViz should be represented in this format
    measure
        Describes which measure is assigned to edges in direcly follows graph (frequency/performance)
    max_no_of_edges_in_diagram
        Maximum number of edges in the diagram allowed for visualization
    start_activities
        Start activities of the log
    end_activities
        End activities of the log
    serv_time
        For each activity, the service time in the log
    font_size
        Size of the text on the activities/edges
    bgcolor
        Background color of the visualization (i.e., 'transparent', 'white', ...)
    rankdir
        Direction of the graph ("LR" for left-to-right; "TB" for top-to-bottom)

    Returns
    -----------
    viz
        Digraph object
    """
    if start_activities is None:
        start_activities = []
    if end_activities is None:
        end_activities = []

    filename = tempfile.NamedTemporaryFile(suffix='.gv')
    filename.close()

    viz = Digraph("", filename=filename.name, engine='dot', graph_attr={'bgcolor': bgcolor, 'rankdir': rankdir})

    # first, remove edges in diagram that exceeds the maximum number of edges in the diagram
    dfg_key_value_list = []
    for edge in dfg:
        dfg_key_value_list.append([edge, dfg[edge]])
    # more fine grained sorting to avoid that edges that are below the threshold are
    # undeterministically removed
    dfg_key_value_list = sorted(dfg_key_value_list, key=lambda x: (x[1], x[0][0], x[0][1]), reverse=True)
    dfg_key_value_list = dfg_key_value_list[0:min(len(dfg_key_value_list), max_no_of_edges_in_diagram)]
    dfg_allowed_keys = [x[0] for x in dfg_key_value_list]
    dfg_keys = list(dfg.keys())
    for edge in dfg_keys:
        if edge not in dfg_allowed_keys:
            del dfg[edge]


    activities_count_int = copy(activities_count)

    activities_in_dfg = set(activities_count)

    # represent nodes
    viz.attr('node', shape='box')

    if len(activities_in_dfg) == 0:
        activities_to_include = sorted(list(set(activities_count_int)))
    else:
        # take unique elements as a list not as a set (in this way, nodes are added in the same order to the graph)
        activities_to_include = sorted(list(set(activities_in_dfg)))

    activities_map = {}

    for act in activities_to_include:
        viz.node(str(hash(act)), act, fontsize=font_size)
        activities_map[act] = str(hash(act))

    # make edges addition always in the same order
    dfg_edges = sorted(list(dfg.keys()))

    # represent edges
    for edge in dfg_edges:
        label = str(dfg[edge])
        viz.edge(str(hash(edge[0])), str(hash(edge[1])), fontsize=font_size, penwidth="2.0")

    start_activities_to_include = [act for act in start_activities if act in activities_map]
    end_activities_to_include = [act for act in end_activities if act in activities_map]

    if start_activities_to_include:
        viz.node("@@startnode", "START", style="filled", fillcolor="lightgrey", fontsize=font_size)
        for act in start_activities_to_include:
            label = str(start_activities[act]) if isinstance(start_activities, dict) and measure == "frequency" else ""
            viz.edge("@@startnode", activities_map[act], fontsize=font_size, penwidth="2.0")

    if end_activities_to_include:
        # <&#9632;>
        viz.node("@@endnode", "END", style="filled", fillcolor="lightgrey", fontsize=font_size)
        for act in end_activities_to_include:
            label = str(end_activities[act]) if isinstance(end_activities, dict) and measure == "frequency" else ""
            viz.edge(activities_map[act], "@@endnode", fontsize=font_size, penwidth="2.0")

    viz.attr(overlap='false')
    viz.attr(fontsize='11')

    viz.format = image_format.replace("html", "plain-ext")

    return viz