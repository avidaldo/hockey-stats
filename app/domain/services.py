import math


def calculate_save_percentage(total_saves: int, total_shots_received: int) -> float:
    if total_shots_received == 0:
        return math.nan
    return total_saves / total_shots_received
