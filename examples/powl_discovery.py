import pm4py
import powl
from powl.conversion.variants.to_bpmn_with_resources import apply as to_bpmn_with_resources

def execute_script():

    # Read event log (csv, xes, or xes.gz)
    log  = powl.import_event_log(r"./examples/running-example.csv")

    # Discover POWL 2.0 model
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0)

    # View the discovered model
    powl.view(model)

    # Export visualization
    powl.save_visualization(model, file_path=r"./examples/powl_vis.svg")

    # Convert into a PM4Py Petri net
    petri_net, initial_marking, final_marking = powl.convert_to_petri_net(model)
    pm4py.view_petri_net(petri_net, initial_marking, final_marking, format="SVG")

    # Convert into a PM4Py BPMN model
    """

    lane_data = {
        'Lane1' : ['register request', 'reinitiate request', 'pay compensation', 'reject request', 'examine casually', 'examine thoroughly', 'check ticket', 'decide'],
    }
    pool_data = {
        'Pool1' : ['Lane1']
        }
    """
    lane_data = {
        'Lane1' : ['register request', 'reinitiate request', 'pay compensation', 'reject request'],
        'Lane2' : ['examine casually', 'examine thoroughly'],
        'Lane3' : ['check ticket', 'decide']
    }
    pool_data = {
        'Pool1' : ['Lane1', 'Lane2'],
        'Pool2' : ['Lane3']
        }

    bpmn_model = to_bpmn_with_resources(pool_data, lane_data, model)
    # export it as .bpmn
    with open(r"./examples/powl_bpmn.bpmn", "w") as f:
        f.write(bpmn_model)

if __name__ == "__main__":
    execute_script()
