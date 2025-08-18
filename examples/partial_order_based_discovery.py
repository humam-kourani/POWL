import pm4py
import powl

def execute_script():

    # Read event log (csv, xes, or xes.gz)
    log = powl.import_event_log(r"../examples/hospital.csv")

    # Discover POWL model
    model = powl.discover_from_partially_ordered_log(log)

    # View the discovered model
    powl.view(model)

    # Export visualization
    powl.save_visualization(model, file_path=r"../examples/powl_vis.svg")

    # Convert into a PM4Py Petri net
    petri_net, initial_marking, final_marking = powl.convert_to_petri_net(model)
    pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")

    # Convert into a PM4Py BPMN model
    bpmn = powl.convert_to_bpmn(model)
    pm4py.view_bpmn(bpmn, format="SVG")

if __name__ == "__main__":
    execute_script()
