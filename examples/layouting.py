import os

import powl

from powl.visualization.bpmn.layout import layout_bpmn


def example_1():
    log = powl.import_event_log(r"./examples/running-example.csv")
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0)
    bpmn = powl.convert_to_bpmn(model)
    # Layout BPMN model
    laid_out_bpmn = layout_bpmn(bpmn)
    # export it as .bpmn
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bpmn_path = os.path.join(current_dir, "powl_bpmn_laid_out.bpmn")
    with open(bpmn_path, "w") as f:
        f.write(laid_out_bpmn)


if __name__ == "__main__":
    example_1()
