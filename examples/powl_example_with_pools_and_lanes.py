import powl
from powl.objects.obj import Transition, DecisionGraph, BinaryRelation
def generate_process():
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

generate_process()
    