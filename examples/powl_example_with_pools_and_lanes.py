import os

import powl
from powl.conversion.variants.to_bpmn_with_resources import (
    apply as to_bpmn_with_resources,
)
from powl.objects.obj import (
    BinaryRelation,
    DecisionGraph,
    Operator,
    OperatorPOWL,
    SilentTransition,
    Transition,
)


def generate_process_1():
    order_coffee = Transition("Order Coffee", "Customer", "Customer")
    pay = Transition("Pay", "Customer", "Customer")
    prepare_coffee = Transition("Prepare Coffee", "Cafe", "Customer")
    serve_coffee = Transition("Serve Coffee", "Cafe", "Barista")
    none = SilentTransition()
    serve_coffee = OperatorPOWL(Operator.XOR, [serve_coffee, none])
    # Create decision graph
    binary_relation = BinaryRelation([order_coffee, pay, prepare_coffee, serve_coffee])
    binary_relation.add_edge(order_coffee, pay)
    binary_relation.add_edge(pay, prepare_coffee)
    binary_relation.add_edge(prepare_coffee, serve_coffee)

    dg = DecisionGraph(
        binary_relation, start_nodes=[order_coffee], end_nodes=[serve_coffee]
    ).simplify()
    # Visualize it
    powl.view(dg)
    bpmn = powl.convert_to_bpmn(dg)
    from powl.visualization.bpmn.layout import layout_bpmn

    bpmn_no_pool_lanes = layout_bpmn(bpmn)
    # Export it as .bpmn with pools and lanes
    with open("coffee_shop_process_no_pools_lanes.bpmn", "w") as f:
        f.write(bpmn_no_pool_lanes)

    bpmn_model = to_bpmn_with_resources(
        {
            "Order Coffee": ("Customer Pool", "Customer Lane"),
            "Pay": ("Customer Pool", "Customer Lane"),
            "Prepare Coffee": ("Cafe Pool", "Cafe Lane"),
            "Serve Coffee": ("Cafe Pool", "Barista Lane"),
        },
        dg,
    )
    with open("coffee_shop_process.bpmn", "w") as f:
        f.write(bpmn_model)


def generate_process_2():

    log = powl.import_event_log(r"./examples/running-example.csv")
    model = powl.discover(log, dfg_frequency_filtering_threshold=0.0)

    activity_to_pool_lane = {
        "register request": ("P1", "Lane1"),
        "reinitiate request": ("P2", "Lane1"),
        "pay compensation": ("P1", "Lane1"),
        "reject request": ("P1", "Lane1"),
        "examine casually": ("P2", "Lane2"),
        "examine thoroughly": ("P1", "Lane2"),
        "check ticket": ("P2", "Lane3"),
        "decide": ("P1", "Lane3"),
    }

    bpmn_model = to_bpmn_with_resources(activity_to_pool_lane, model)
    # export it as .bpmn
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bpmn_path = os.path.join(current_dir, "powl_bpmn.bpmn")
    with open(bpmn_path, "w") as f:
        f.write(bpmn_model)


if __name__ == "__main__":
    generate_process_2()
