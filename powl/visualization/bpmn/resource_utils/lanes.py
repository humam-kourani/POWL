from typing import List, Tuple


class Lane:
    def __init__(
        self,
        up_left: Tuple[int, int],
        down_right: Tuple[int, int],
        name: str,
        activities: List[str],
    ):
        self.up_left = up_left
        self.down_right = down_right
        self.name = name
        self.activities = activities
        self.elements = []

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

    def get_activities(self) -> List[str]:
        return self.activities

    def get_elements(self) -> List[str]:
        return self.elements

    def add_element(self, element: str) -> None:
        self.elements.append(element)

    def has_element(self, element: str) -> bool:
        return element in self.elements
