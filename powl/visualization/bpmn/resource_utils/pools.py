from typing import List, Tuple

from powl.visualization.bpmn.resource_utils.lanes import Lane


class Pool:
    def __init__(
        self,
        up_left: Tuple[int, int],
        down_right: Tuple[int, int],
        name: str,
        lanes: List[Lane],
    ):
        self.up_left = up_left
        self.down_right = down_right
        self.name = name
        self.lanes = lanes

    def get_up_left(self) -> Tuple[int, int]:
        return self.up_left

    def set_up_left(self, up_left: Tuple[int, int]) -> None:
        self.up_left = up_left

    def get_down_right(self) -> Tuple[int, int]:
        return self.down_right

    def set_down_right(self, down_right: Tuple[int, int]) -> None:
        self.down_right = down_right

    def get_name(self) -> str:
        return self.name

    def get_lanes(self) -> List[Lane]:
        return self.lanes
