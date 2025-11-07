import pm4py
import powl
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant


def execute_script():

    # Read event log (csv, xes, or xes.gz)
    log  = powl.import_event_log(r"../examples/running-example.csv")
    # log = powl.import_event_log(r"C:\Users\kourani\OneDrive - Fraunhofer\FIT\Unfiltered XES Logs\Sepsis Cases - Event Log.xes.gz")

    # Discover POWL 2.0 model
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0, variant=POWLDiscoveryVariant.DECISION_GRAPH_CYCLIC, simplify=False)

    # View the discovered model
    powl.view(model, use_frequency_tags=False)




    # Export visualization
    # powl.save_visualization(model, file_path=r"../examples/powl_vis.svg")

    # Convert into a PM4Py Petri net
    petri_net, initial_marking, final_marking = powl.convert_to_petri_net(model)
    pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")

    # petri_net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
    # pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")
    pm4py.write_pnml(petri_net, initial_marking, final_marking, file_path=r"C:\Users\kourani\Downloads\non_fitting_example.pnml")

    fitness = pm4py.fitness_alignments(log, petri_net, initial_marking, final_marking)
    print(fitness)

    # aligned_traces = pm4py.conformance_diagnostics_alignments(log, petri_net, initial_marking, final_marking)
    # for t in aligned_traces:
    #     if t["fitness"] < 1:
    #         print(t)
    precision = pm4py.precision_alignments(log, petri_net, initial_marking, final_marking)
    print(precision)

    # Convert into a PM4Py BPMN model
    bpmn = pm4py.convert_to_bpmn(petri_net, initial_marking, final_marking)
    pm4py.view_bpmn(bpmn, format="SVG")

if __name__ == "__main__":
    execute_script()
