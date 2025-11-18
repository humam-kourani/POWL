import importlib.resources
import tempfile
from enum import Enum

from graphviz import Digraph
from pm4py.objects.process_tree.obj import Operator
from pm4py.util import exec_utils

from powl.objects.obj import (
    DecisionGraph,
    EndNode,
    FrequentTransition,
    OperatorPOWL,
    POWL,
    SilentTransition,
    StartNode,
    StrictPartialOrder,
    Transition,
)

min_width = "1.5"  # Set the minimum width in inches
fillcolor = "#fcfcfc"
opacity_change_ratio = 0.02
FONT_SIZE = "18"
PEN_WIDTH = "1"


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

    filename = tempfile.NamedTemporaryFile(suffix=".gv")

    viz = Digraph("powl", filename=filename.name, engine="dot")
    viz.attr("node", shape="ellipse", fixedsize="false")
    viz.attr(nodesep="1")
    viz.attr(ranksep="1")
    viz.attr(compound="true")
    viz.attr(overlap="scale")
    viz.attr(splines="true")
    viz.attr(rankdir="TB")
    viz.attr(style="filled")
    viz.attr(fillcolor=fillcolor)

    color_map = exec_utils.get_param_value(Parameters.COLOR_MAP, {}, {})

    repr_powl(powl, viz, color_map, level=0, skip_order=False, loop_order=False)
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


def get_block_id(powl):
    if (
        isinstance(powl, OperatorPOWL)
        or isinstance(powl, StrictPartialOrder)
        or isinstance(powl, DecisionGraph)
    ):
        return "cluster_" + str(id(powl))
    else:
        raise Exception(f"Unknown POWL type {type(powl)}!")


def add_operator_edge(vis, current_node_id, child_ids, directory="none", style=""):
    child_base_id, block_id = child_ids
    if block_id:
        vis.edge(
            current_node_id,
            child_base_id,
            dir=directory,
            lhead=block_id,
            style=style,
            minlen="2",
            penwidth=PEN_WIDTH,
        )
    else:
        vis.edge(
            current_node_id,
            child_base_id,
            dir=directory,
            style=style,
            penwidth=PEN_WIDTH,
        )


def add_order_edge(
    block, child_1_ids, child_2_ids, directory="forward", color="black", style=""
):
    child_1_base_id, block_id_1 = child_1_ids
    child_2_base_id, block_id_2 = child_2_ids

    if block_id_1:
        if block_id_2:
            block.edge(
                child_1_base_id,
                child_2_base_id,
                dir=directory,
                color=color,
                style=style,
                ltail=block_id_1,
                lhead=block_id_2,
                minlen="2",
                penwidth=PEN_WIDTH,
            )
        else:
            block.edge(
                child_1_base_id,
                child_2_base_id,
                dir=directory,
                color=color,
                style=style,
                ltail=block_id_1,
                minlen="2",
                penwidth=PEN_WIDTH,
            )
    else:
        if block_id_2:
            block.edge(
                child_1_base_id,
                child_2_base_id,
                dir=directory,
                color=color,
                style=style,
                lhead=block_id_2,
                minlen="2",
                penwidth=PEN_WIDTH,
            )
        else:
            block.edge(
                child_1_base_id,
                child_2_base_id,
                dir=directory,
                color=color,
                style=style,
                penwidth=PEN_WIDTH,
            )


def mark_block(block, skip_order, loop_order):
    if skip_order:
        if loop_order:
            with importlib.resources.path(
                "pm4py.visualization.powl.variants.icons", "skip-loop-tag.svg"
            ) as gimg:
                image = str(gimg)
                block.attr(
                    label=f"""<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                        <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                        </TABLE>>"""
                )
                block.attr(labeljust="r")
        else:
            with importlib.resources.path(
                "pm4py.visualization.powl.variants.icons", "skip-tag.svg"
            ) as gimg:
                image = str(gimg)
                block.attr(
                    label=f"""<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                        <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                        </TABLE>>"""
                )
                block.attr(labeljust="r")
    elif loop_order:
        with importlib.resources.path(
            "pm4py.visualization.powl.variants.icons", "loop-tag.svg"
        ) as gimg:
            image = str(gimg)
            block.attr(
                label=f"""<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
                                    <TR><TD WIDTH="55" HEIGHT="27" FIXEDSIZE="TRUE"><IMG SRC="{image}" SCALE="BOTH"/></TD></TR>
                                    </TABLE>>"""
            )
            block.attr(labeljust="r")
    else:
        block.attr(label="")


def repr_powl(powl, viz, color_map, level, skip_order, loop_order):
    font_size = FONT_SIZE
    this_node_id = str(id(powl))

    current_color = darken_color(fillcolor, amount=opacity_change_ratio * level)
    block_id = None

    if isinstance(powl, FrequentTransition):
        label = powl.activity
        if powl.skippable:
            if powl.selfloop:
                with importlib.resources.path(
                    "powl.visualization.powl.variants.icons", "skip-loop-tag.svg"
                ) as gimg:
                    image = str(gimg)
                    viz.node(
                        this_node_id,
                        label="\n" + label,
                        imagepos="tr",
                        image=image,
                        shape="box",
                        width=min_width,
                        fontsize=font_size,
                        style="filled",
                        fillcolor=current_color,
                    )
            else:
                with importlib.resources.path(
                    "powl.visualization.powl.variants.icons", "skip-tag.svg"
                ) as gimg:
                    image = str(gimg)
                    viz.node(
                        this_node_id,
                        label="\n" + label,
                        imagepos="tr",
                        image=image,
                        shape="box",
                        width=min_width,
                        fontsize=font_size,
                        style="filled",
                        fillcolor=current_color,
                    )
        else:
            if powl.selfloop:
                with importlib.resources.path(
                    "powl.visualization.powl.variants.icons", "loop-tag.svg"
                ) as gimg:
                    image = str(gimg)
                    viz.node(
                        this_node_id,
                        label="\n" + label,
                        imagepos="tr",
                        image=image,
                        shape="box",
                        width=min_width,
                        fontsize=font_size,
                        style="filled",
                        fillcolor=current_color,
                    )
            else:
                viz.node(
                    this_node_id,
                    label=label,
                    shape="box",
                    width=min_width,
                    fontsize=font_size,
                    style="filled",
                    fillcolor=current_color,
                )
    elif isinstance(powl, Transition):
        if isinstance(powl, SilentTransition):
            viz.node(
                this_node_id,
                label="",
                style="filled",
                fillcolor="black",
                shape="square",
                width="0.3",
                height="0.3",
                fixedsize="true",
            )
        else:
            label = f"<{str(powl.label)}"
            if powl._role is not None and powl._organization is not None:
                # Add a label to the box
                label += f"""<br/><font color="grey" point-size="10">({powl._organization}, {powl._role})</font><br/>"""
            elif powl._organization is not None:
                # Add a label to the box
                label += f"""<br/><font color="grey" point-size="10">({powl._organization})</font><br/>"""
            elif powl._role is not None:
                # Add a label to the box
                label += f"""<br/><font color="grey" point-size="10">({powl._role})</font><br/>"""

            label += ">"

            viz.node(
                this_node_id,
                label,
                shape="box",
                fontsize=font_size,
                width=min_width,
                style="filled",
                fillcolor=current_color,
            )

    elif isinstance(powl, StrictPartialOrder):
        transitive_reduction = powl.order.get_transitive_reduction()
        block_id = get_block_id(powl)
        child_id_map = {}
        with viz.subgraph(name=block_id) as block:
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(fillcolor=current_color)

            mark_block(block, skip_order, loop_order)

            this_node_id = make_anchor(block, block_id)

            for child in powl.children:
                child_id_map[child] = repr_powl(
                    child,
                    block,
                    color_map,
                    level=level + 1,
                    skip_order=False,
                    loop_order=False,
                )
            for child in powl.children:
                for child2 in powl.children:
                    if transitive_reduction.is_edge(child, child2):
                        add_order_edge(block, child_id_map[child], child_id_map[child2])

    elif isinstance(powl, StartNode) or isinstance(powl, EndNode):
        with importlib.resources.path(
            "powl.visualization.powl.variants.icons", "gate_navy.svg"
        ) as gimg:
            xor_image = str(gimg)
            viz.node(
                this_node_id,
                label="",
                shape="diamond",
                color="navy",
                width="0.6",
                height="0.6",
                fixedsize="true",
                image=xor_image,
            )
    elif isinstance(powl, DecisionGraph):
        if len(powl.children) == 1:
            child = powl.children[0]
            if (
                isinstance(child, StrictPartialOrder)
                or isinstance(child, DecisionGraph)
                or isinstance(child, OperatorPOWL)
            ):
                if powl.order.is_edge(powl.start, powl.end):
                    skip_order = True
                if powl.order.is_edge(child, child):
                    loop_order = True

                return repr_powl(
                    child,
                    viz,
                    color_map,
                    level=level,
                    skip_order=skip_order,
                    loop_order=loop_order,
                )

        block_id = get_block_id(powl)
        child_id_map = {}
        with viz.subgraph(name=block_id) as block:
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(fillcolor=current_color)

            mark_block(block, skip_order, loop_order)

            this_node_id = make_anchor(block, block_id)

            for child in powl.order.nodes:
                child_id_map[child] = repr_powl(
                    child,
                    block,
                    color_map,
                    level=level + 1,
                    skip_order=False,
                    loop_order=False,
                )

            for child in powl.order.nodes:
                for child2 in powl.order.nodes:
                    if powl.order.is_edge(child, child2):
                        add_order_edge(
                            block,
                            child_id_map[child],
                            child_id_map[child2],
                            color="navy",
                            style="dashed",
                        )

    elif isinstance(powl, OperatorPOWL):
        if powl.operator == Operator.XOR:
            silent_children = [
                child for child in powl.children if isinstance(child, SilentTransition)
            ]
            if len(silent_children) > 0:
                other_children = [
                    child
                    for child in powl.children
                    if not isinstance(child, SilentTransition)
                ]
                if len(other_children) == 1:
                    child = other_children[0]
                    if (
                        isinstance(child, StrictPartialOrder)
                        or isinstance(child, DecisionGraph)
                        or isinstance(child, OperatorPOWL)
                    ):
                        return repr_powl(
                            child,
                            viz,
                            color_map,
                            level=level,
                            skip_order=True,
                            loop_order=loop_order,
                        )
                elif len(other_children) > 1:
                    children_powl = OperatorPOWL(
                        operator=powl.operator, children=other_children
                    )
                    return repr_powl(
                        children_powl,
                        viz,
                        color_map,
                        level=level,
                        skip_order=True,
                        loop_order=loop_order,
                    )

        if powl.operator == Operator.LOOP:
            do = powl.children[0]
            redo = powl.children[1]
            if isinstance(do, SilentTransition) and (
                isinstance(redo, StrictPartialOrder)
                or isinstance(redo, DecisionGraph)
                or isinstance(redo, OperatorPOWL)
            ):
                return repr_powl(
                    redo, viz, color_map, level=level, skip_order=True, loop_order=True
                )
            if isinstance(redo, SilentTransition) and (
                isinstance(do, StrictPartialOrder)
                or isinstance(do, DecisionGraph)
                or isinstance(do, OperatorPOWL)
            ):
                return repr_powl(
                    do,
                    viz,
                    color_map,
                    level=level,
                    loop_order=True,
                    skip_order=skip_order,
                )

        block_id = get_block_id(powl)
        with viz.subgraph(name=block_id) as block:
            block.attr(margin="20,20")
            block.attr(style="filled")
            block.attr(fillcolor=current_color)
            mark_block(block, skip_order, loop_order)
            if powl.operator == Operator.LOOP:
                with importlib.resources.path(
                    "powl.visualization.powl.variants.icons", "loop.svg"
                ) as gimg:
                    image = str(gimg)
                    block.node(
                        this_node_id,
                        image=image,
                        label="",
                        fontsize=font_size,
                        width="0.4",
                        height="0.4",
                        fixedsize="true",
                    )
                    anchor_id = make_anchor(block, block_id)
                do = powl.children[0]
                redo = powl.children[1]
                do_id = repr_powl(
                    do,
                    block,
                    color_map,
                    level=level + 1,
                    skip_order=False,
                    loop_order=False,
                )
                add_operator_edge(block, this_node_id, do_id)
                redo_id = repr_powl(
                    redo,
                    block,
                    color_map,
                    level=level + 1,
                    skip_order=False,
                    loop_order=False,
                )
                add_operator_edge(block, this_node_id, redo_id, style="dashed")
            elif powl.operator == Operator.XOR:
                with importlib.resources.path(
                    "powl.visualization.powl.variants.icons", "xor.svg"
                ) as gimg:
                    image = str(gimg)
                    block.node(
                        this_node_id,
                        image=image,
                        label="",
                        fontsize=font_size,
                        width="0.4",
                        height="0.4",
                        fixedsize="true",
                    )
                    anchor_id = make_anchor(block, block_id)
                for child in powl.children:
                    child_id = repr_powl(
                        child,
                        block,
                        color_map,
                        level=level + 1,
                        skip_order=False,
                        loop_order=False,
                    )
                    add_operator_edge(block, this_node_id, child_id)
            else:
                raise NotImplementedError
            this_node_id = anchor_id
    else:
        raise Exception(f"Unknown POWL operator: {type(powl)}")

    return this_node_id, block_id


def darken_color(color, amount):
    """Darkens the given color by the specified amount"""
    import matplotlib.colors as mcolors

    amount = min(0.3, amount)

    rgb = mcolors.to_rgb(color)
    darker = [x * (1 - amount) for x in rgb]
    return mcolors.to_hex(darker)


def make_anchor(block, block_id):
    anchor_id = f"anchor_{block_id}"
    block.node(
        anchor_id,
        label="",
        shape="point",
        width="0.01",
        height="0.01",
        fixedsize="true",
        style="invis",
    )
    return anchor_id
