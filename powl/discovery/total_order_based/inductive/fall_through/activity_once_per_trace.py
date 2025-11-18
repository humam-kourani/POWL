from pm4py.algo.discovery.inductive.fall_through.activity_once_per_trace import (
    ActivityOncePerTraceUVCL,
)

from powl.discovery.total_order_based.inductive.fall_through.activity_concurrent import (
    POWLActivityConcurrentUVCL,
)


class POWLActivityOncePerTraceUVCL(
    ActivityOncePerTraceUVCL, POWLActivityConcurrentUVCL
):
    pass
