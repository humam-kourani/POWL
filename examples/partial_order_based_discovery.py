import os

import pm4py
import powl

def execute_script():

    # Read event log (csv, xes, or xes.gz)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "hospital.csv")
    log = powl.import_event_log(path)

    # Discover POWL model
    model = powl.discover_from_partially_ordered_log(log)

    # View the discovered model
    powl.view(model)

    # Export visualization
    image_path = os.path.join(current_dir, "powl_vis.svg")
    powl.save_visualization(model, file_path=image_path)

    # Convert into a PM4Py Petri net
    petri_net, initial_marking, final_marking = powl.convert_to_petri_net(model)
    pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")

    # Convert into a PM4Py BPMN model
    bpmn = powl.convert_to_bpmn(model)
    pm4py.view_bpmn(bpmn, format="SVG")

if __name__ == "__main__":
    execute_script()
