import pm4py
import powl
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant

def execute_script():

    # Read event log (csv, xes, or xes.gz)
    log  = powl.import_event_log(r"./examples/running-example.csv")

    # Discover POWL 2.0 model
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0, variant=POWLDiscoveryVariant.DECISION_GRAPH_CYCLIC)

    # View the discovered model
    powl.view(model)

    # Export visualization
    powl.save_visualization(model, file_path=r"./examples/powl_vis.svg")

    # Convert into a PM4Py Petri net
    petri_net, initial_marking, final_marking = powl.convert_to_petri_net(model)
    pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")

    # Convert into a PM4Py BPMN model
    bpmn = pm4py.convert_to_bpmn(petri_net, initial_marking, final_marking)
    pm4py.view_bpmn(bpmn, format="SVG")

if __name__ == "__main__":
    execute_script()
