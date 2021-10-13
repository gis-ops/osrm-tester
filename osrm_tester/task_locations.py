from random import uniform
from typing import Optional, List, Tuple

from haversine import haversine, Unit


LOWERLIMIT = None
UPPERLIMIT = None
bbox: Optional[List[float]] = None


def init(b: List[float], lower: int, upper: int):
    """Set the global attributes"""
    global bbox, LOWERLIMIT, UPPERLIMIT
    bbox = b.copy()
    LOWERLIMIT = lower
    UPPERLIMIT = upper


def work(_):
    assert bbox is not None

    p1: Tuple[float, float] = (
        round(uniform(bbox[0], bbox[2]), 6),
        round(uniform(bbox[1], bbox[3]), 6),
    )
    # Conform with the imposed limits
    while True:
        p2 = (round(uniform(bbox[0], bbox[2]), 6), round(uniform(bbox[1], bbox[3]), 6))
        dist = haversine(reversed(p1), reversed(p2), unit=Unit.METERS)
        if dist > UPPERLIMIT or dist < LOWERLIMIT:
            break

    return p1, p2
