import pm4py
import powl


def execute_script():

    # Read object centric event log (ocel 1.0 or ocel 2.0)
    object_centric_log = powl.import_ocel(
        r"C:\Users\kourani\OneDrive - Fraunhofer\FIT\oc_powl\oc_logs\recruiting.jsonocel"
    )

    object_centric_pn = powl.discover_petri_net_from_ocel(object_centric_log)
    pm4py.view_ocpn(object_centric_pn, format="SVG")


if __name__ == "__main__":
    execute_script()
