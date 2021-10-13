from multiprocessing import Lock
from statistics import mean
from typing import Optional, Union

import pyosrm
import requests

from .utils.misc import delimit_tuple
from .logger import LOGGER

# protect against missing OSRM bindings
try:
    from pyosrm import PyOSRM
except (ModuleNotFoundError, ImportError):
    pass

# global(s) for multiprocessing func
host: Optional[str] = None
action: Optional[str] = None
report: Optional[bool] = None
router: Optional[pyosrm.PyOSRM] = None


def init(a: str, h: str, c: str, r: bool, lock: Lock) -> None:
    """Initialize each process with its own OSRM file"""
    global host, action, report, router

    action = a
    if r:
        report = r
    if h:
        host = h
    if c:
        lock.acquire()
        try:
            router = PyOSRM(c, use_shared_memory=False, algorithm="MLD")
        finally:
            lock.release()


def work(params) -> Union[None, float]:
    """Return the distance in meters or None (to be filtered by caller)"""
    try:
        # either HTTP or bindings
        if host:
            path = action if action == "route" else "sources_to_targets"
            params_str = delimit_tuple(
                tuple((delimit_tuple(x) for x in params)), delimiter=";"
            )
            route = requests.get(f"{host}/{path}/v1/driving/{params_str}")
        else:
            route = router.route(params) if action == "route" else None
    except (RuntimeError, requests.exceptions.BaseHTTPError):
        return None

    if report:
        result = route.json()
        if action == "route":
            try:
                dist = sum([x["distance"] for x in result["routes"]])
            except KeyError:
                LOGGER.critical(
                    f"No route was found from {params[0]} to {params[1]}. "
                    f"Try regenerating the locations or specify a more narrow bounding box."
                )
                return None
        else:
            dists = [
                inner["distance"]
                for outer in route["sources_to_targets"]
                for inner in outer
            ]
            dist: float = mean(filter(lambda x: x is not None, dists))

        return dist
