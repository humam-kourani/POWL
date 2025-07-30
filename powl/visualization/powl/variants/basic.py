import importlib.resources
import tempfile
from enum import Enum
from graphviz import Digraph
from pm4py.objects.process_tree.obj import Operator
from pm4py.util import exec_utils
from powl.objects.obj import POWL, Transition, SilentTransition, StrictPartialOrder, OperatorPOWL, \
    FrequentTransition, DecisionGraph, StartNode, EndNode

OPERATOR_BOXES = True
FREQUENCY_TAG_IMAGES = True

min_width = "1.5"  # Set the minimum width in inches
min_height = "0.5"
fillcolor = "#fcfcfc"
opacity_change_ratio = 0.02
FONT_SIZE = "20"
PEN_WIDTH = "2.0"


class Parameters(Enum):
    FORMAT = "format"
    COLOR_MAP = "color_map"
    ENABLE_DEEPCOPY = "enable_deepcopy"
    FONT_SIZE = "font_size"
    BGCOLOR = "bgcolor"


def apply(powl: POWL) -> Digraph:
    """
    Obtain a POWL model representation through GraphViz

    Parameters
    -----------
    powl
        POWL model

    Returns
    -----------
    gviz
        GraphViz Digraph
    """

    filename = tempfile.NamedTemporaryFile(suffix='.gv')

    viz = Digraph("powl", filename=filename.name, engine='dot')
    viz.attr('node', shape='ellipse', fixedsize='false')
    viz.attr(nodesep='1')
    viz.attr(ranksep='1')
    viz.attr(compound='true')
    viz.attr(overlap='scale')
    viz.attr(splines='true')
    viz.attr(rankdir='TB')
    viz.attr(style="filled")
    viz.attr(fillcolor=fillcolor)

    color_map = exec_utils.get_param_value(Parameters.COLOR_MAP, {}, {})

    repr_powl(powl, viz, color_map, level=0)
    viz.format = "svg"

    return viz


def get_color(node, color_map):
    """
    Gets a color for a node from the color map

    Parameters
    --------------
    node
        Node
    color_map
        Color map
    """
    if node in color_map:
        return color_map[node]
    return "black"


def get_id_base(powl):
    if isinstance(powl, Transition):
        return str(id(powl))
    if isinstance(powl, OperatorPOWL):
        for node in powl.children:
            if not isinstance(node, SilentTransition):
                return get_id_base(node)
    elif isinstance(powl, StrictPartialOrder):
        for node in powl.children:
            return get_id_base(node)
    elif isinstance(powl, DecisionGraph):
        for node in powl.children:
            return get_id_base(node)
    else:
        raise Exception("Unknown POWL type!")


def get_id(powl):
    if isinstance(powl, Transition):
        return str(id(powl))
    elif isinstance(powl, OperatorPOWL):
        if OPERATOR_BOXES:
            return "cluster_" + str(id(powl))
        else:
            return "clusterINVIS_" + str(id(powl))
    elif isinstance(powl, StrictPartialOrder):
        return "cluster_" + str(id(powl))
    elif isinstance(powl, DecisionGraph):
        return "cluster_" + str(id(powl))
    else:
        raise Exception("Unknown POWL type!")


def add_operator_edge(vis, current_node_id, child, directory='none', style=""):
    child_id = get_id(child)
    if child_id.startswith("cluster_"):
        vis.edge(current_node_id, get_id_base(child), dir=directory, lhead=child_id, style=style, minlen='2', penwidth=PEN_WIDTH)
    else:
        vis.edge(current_node_id, get_id_base(child), dir=directory, style=style, penwidth=PEN_WIDTH)


def add_order_edge(block, child_1, child_2, directory='forward', color="black", style=""):
    child_id_1 = get_id(child_1)
    child_id_2 = get_id(child_2)
    if child_id_1.startswith("cluster_"):
        if child_id_2.startswith("cluster_"):
            block.edge(get_id_base(child_1), get_id_base(child_2), dir=directory, color=color, style=style,
                       ltail=child_id_1, lhead=child_id_2, minlen='2', penwidth=PEN_WIDTH)
        else:
            block.edge(get_id_base(child_1), get_id_base(child_2), dir=directory, color=color, style=style,
                       ltail=child_id_1, minlen='2', penwidth=PEN_WIDTH)
    else:
        if child_id_2.startswith("cluster_"):
            block.edge(get_id_base(child_1), get_id_base(child_2), dir=directory, color=color, style=style,
                       lhead=child_id_2, minlen='2', penwidth=PEN_WIDTH)
        else:
            block.edge(get_id_base(child_1), get_id_base(child_2), dir=directory, color=color, style=style, penwidth=PEN_WIDTH)


def repr_powl(powl, viz, color_map, level, skip_order=False, loop_order=False, block_id=None):
    font_size = FONT_SIZE
    this_node_id = str(id(powl))

    current_color = darken_color(fillcolor, amount=opacity_change_ratio * level)

    if isinstance(powl, FrequentTransition):
        label = powl.activity
        if powl.skippable:
            if powl.selfloop:
                with importlib.resources.path("powl.visualization.powl.variants.icons", "skip-loop-tag.svg") as gimg:
                    image = str(gimg)
                    viz.node(this_node_id, label='\n' + label, imagepos='tr', image=image,
                             shape='box', width=min_width, fontsize=font_size, style='filled', fillcolor=current_color)
            else:
                with importlib.resources.path("powl.visualization.powl.variants.icons", "skip-tag.svg") as gimg:
                    image = str(gimg)
                    viz.node(this_node_id, label='\n' + label, imagepos='tr', image=image,
                             shape='box', width=min_width, fontsize=font_size, style='filled', fillcolor=current_color)
        else:
            if powl.selfloop:
                with importlib.resources.path("powl.visualization.powl.variants.icons", "loop-tag.svg") as gimg:
                    image = str(gimg)
                    viz.node(this_node_id, label='\n' + label, imagepos='tr', image=image,
                             shape='box', width=min_width, fontsize=font_size, style='filled', fillcolor=current_color)
            else:
                viz.node(this_node_id, label=label,
                         shape='box', width=min_width, fontsize=font_size, style='filled', fillcolor=current_color)
    elif isinstance(powl, Transition):
        if isinstance(powl, SilentTransition):
            viz.node(this_node_id, label='', style='filled', fillcolor='black', shape='square',
                     width='0.4', height='0.4', fixedsize="true")
        else:
            viz.node(this_node_id, str(powl.label), shape='box', fontsize=font_size, width=min_width, style='filled',
                     fillcolor=current_color)

    elif isinstance(powl, StrictPartialOrder):
        transitive_reduction = powl.order.get_transitive_reduction()
        if not block_id:
            block_id = get_id(powl)
        with viz.subgraph(name=block_id) as block:
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(label="")
            block.attr(fillcolor=current_color)

            if skip_order:
                if loop_order:
                    with importlib.resources.path("pm4py.visualization.powl.variants.icons",
                                                  "skip-loop-tag.svg") as gimg:
                        image = str(gimg)
                        block.attr(label=f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                                            <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                                            </TABLE>>''')
                        block.attr(labeljust='r')
                else:
                    with importlib.resources.path("pm4py.visualization.powl.variants.icons", "skip-tag.svg") as gimg:
                        image = str(gimg)
                        block.attr(label=f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                                            <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                                            </TABLE>>''')
                        block.attr(labeljust='r')
            elif loop_order:
                with importlib.resources.path("pm4py.visualization.powl.variants.icons", "loop-tag.svg") as gimg:
                    image = str(gimg)
                    block.attr(label=f'''<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                                        <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                                        </TABLE>>''')
                    block.attr(labeljust='r')
            else:
                block.attr(label="")

            for child in powl.children:
                repr_powl(child, block, color_map, level=level + 1)
            for child in powl.children:
                for child2 in powl.children:
                    if transitive_reduction.is_edge(child, child2):
                        add_order_edge(block, child, child2)

    elif isinstance(powl, StartNode) or isinstance(powl, EndNode):
        with importlib.resources.path("powl.visualization.powl.variants.icons", "gate_navy.svg") as gimg:
            xor_image = str(gimg)
            viz.node(this_node_id, label="", shape="diamond", color="navy",
                     width='0.6', height='0.6', fixedsize="true", image=xor_image)
    elif isinstance(powl, DecisionGraph):
        with viz.subgraph(name=get_id(powl)) as block:
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(fillcolor=current_color)
            for child in powl.order.nodes:
                repr_powl(child, block, color_map, level=level + 1)
            for child in powl.order.nodes:
                for child2 in powl.order.nodes:
                    if powl.order.is_edge(child, child2):
                        add_order_edge(block, child, child2, color="navy", style="dashed")

    elif isinstance(powl, OperatorPOWL):
        block_id = get_id(powl)
        if powl.operator == Operator.XOR and len(powl.children) == 2:
            child_0 = powl.children[0]
            child_1 = powl.children[1]
            if isinstance(child_0, SilentTransition) and isinstance(child_1, StrictPartialOrder):
                repr_powl(child_1, viz, color_map, level=level, skip_order=True, block_id=block_id)
                return
            if isinstance(child_1, SilentTransition) and isinstance(child_0, StrictPartialOrder):
                repr_powl(child_0, viz, color_map, level=level, skip_order=True, block_id=block_id)
                return

        if powl.operator == Operator.LOOP:
            do = powl.children[0]
            redo = powl.children[1]
            if isinstance(do, SilentTransition) and isinstance(redo, StrictPartialOrder):
                repr_powl(redo, viz, color_map, level=level, skip_order=True, loop_order=True, block_id=block_id)
                return
            if isinstance(redo, SilentTransition) and isinstance(do, StrictPartialOrder):
                repr_powl(do, viz, color_map, level=level, loop_order=True, block_id=block_id)
                return

        with viz.subgraph(name=block_id) as block:
            block.attr(label="")
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(fillcolor=current_color)
            if powl.operator == Operator.LOOP:
                with importlib.resources.path("powl.visualization.powl.variants.icons", "loop.svg") as gimg:
                    image = str(gimg)
                    block.node(this_node_id, image=image, label="", fontsize=font_size,
                               width='0.5', height='0.5', fixedsize="true")
                do = powl.children[0]
                redo = powl.children[1]
                repr_powl(do, block, color_map, level=level + 1)
                add_operator_edge(block, this_node_id, do)
                repr_powl(redo, block, color_map, level=level + 1)
                add_operator_edge(block, this_node_id, redo, style="dashed")
            elif powl.operator == Operator.XOR:
                with importlib.resources.path("powl.visualization.powl.variants.icons", "xor.svg") as gimg:
                    image = str(gimg)
                    block.node(this_node_id, image=image, label="", fontsize=font_size,
                               width='0.5', height='0.5', fixedsize="true")
                for child in powl.children:
                    repr_powl(child, block, color_map, level=level + 1)
                    add_operator_edge(block, this_node_id, child)
    else:
        raise Exception(f"Unknown POWL operator: {type(powl)}")


def darken_color(color, amount):
    """ Darkens the given color by the specified amount """
    import matplotlib.colors as mcolors
    amount = min(0.3, amount)

    rgb = mcolors.to_rgb(color)
    darker = [x * (1 - amount) for x in rgb]
    return mcolors.to_hex(darker)
