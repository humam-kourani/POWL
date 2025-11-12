import streamlit as st
import streamlit.components.v1 as components
import os

_RELEASE = False

# Set up the component function
component_name = "bpmn_to_svg_converter"
if not _RELEASE:
    _component_func = components.declare_component(
        component_name,
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(component_name, path=build_dir)

def bpmn_to_svg(bpmn_xml: str, key=None) -> str:
    """
    An invisible component that converts a BPMN XML string to an SVG string.
    """
    component_value = _component_func(xml=bpmn_xml, key=key, default=None)
    return component_value
