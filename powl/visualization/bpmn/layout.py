import pm4py
from pm4py.objects.bpmn.exporter.variants.etree import get_xml_string
from pm4py.objects.bpmn.layout import layouter as bpmn_layouter

from powl.visualization.bpmn.resource_utils.layouter import (
    apply_layouting as bpmn_io_layout,
)


def layout_bpmn(bpmn_model: pm4py.objects.bpmn.obj.BPMN) -> str:
    """
    Apply layout to a BPMN model.

    :param bpmn_model: BPMN model as a string or PM4Py BPMN object
    :return: String representation of the layouted BPMN model
    """
    if isinstance(bpmn_model, str):
        raise ValueError("Input must be a PM4Py BPMN object, not a string.")
    layouted_bpmn = bpmn_layouter.apply(bpmn_model)
    bpmn = get_xml_string(layouted_bpmn).decode("utf-8")
    bpmn = bpmn_io_layout(bpmn)
    return bpmn
