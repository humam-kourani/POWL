import powl

def execute_script():
    log = powl.import_event_log(r"../examples/running-example.csv")
    model = powl.discover_from_partially_ordered_log(log)
    powl.view(model)

if __name__ == "__main__":
    execute_script()
