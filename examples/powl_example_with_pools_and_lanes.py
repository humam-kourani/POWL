import powl
from powl.objects.obj import Transition, DecisionGraph, BinaryRelation
from powl.conversion.variants.to_bpmn_with_resources import apply as to_bpmn_with_resources


def generate_process_1():
    order_coffee = Transition("Order Coffee", "Customer", "Customer")
    pay = Transition("Pay", "Customer", "Customer")
    prepare_coffee = Transition("Prepare Coffee", "Cafe", "Barista")
    serve_coffee = Transition("Serve Coffee", "Cafe", "Barista")
    # Create decision graph
    binary_relation = BinaryRelation([order_coffee, pay, prepare_coffee, serve_coffee])
    binary_relation.add_edge(order_coffee, pay)
    binary_relation.add_edge(pay, prepare_coffee)
    binary_relation.add_edge(prepare_coffee, serve_coffee)

    dg = DecisionGraph(binary_relation, start_nodes=[order_coffee], end_nodes=[serve_coffee]).simplify()
    # Visualize it
    powl.view(dg)

def generate_process_2():

    log  = powl.import_event_log(r"./examples/running-example.csv")
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0)
    

    activity_to_pool_lane = {
        'register request' : ("P1", 'Lane1'),
        'reinitiate request' : ("P2", 'Lane1'),
        'pay compensation' : ("P1", 'Lane1'),
        'reject request' : ("P1", 'Lane1'),
        'examine casually' : ("P2", 'Lane2'),
        'examine thoroughly' : ("P1", 'Lane2'),
        'check ticket' : ("P2", 'Lane3'),
        'decide' : ("P1", 'Lane3'),
    }

    bpmn_model = to_bpmn_with_resources(activity_to_pool_lane, model)
    # export it as .bpmn
    with open(r"./examples/powl_bpmn.bpmn", "w") as f:
        f.write(bpmn_model)


if __name__ == "__main__":
    generate_process_1()
