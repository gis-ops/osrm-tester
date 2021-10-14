import multiprocessing as mp
from io import TextIOWrapper
from ast import literal_eval
from statistics import mean, stdev
import time

import click
from haversine import haversine, Unit

from .logger import LOGGER, map_verbosity
from .__version__ import __version__
from .utils.click import MutuallyExclusiveOption, DefaultCommand
from .utils.misc import bbox_is_valid
from .defaults import Defaults
from . import task_locations
from . import task_action

# protect against missing OSRM bindings
# and raise when not found but binding usage requested
OSRM_FOUND = True
try:
    import pyosrm  # noqa: F401
except (ModuleNotFoundError, ImportError):
    OSRM_FOUND = False


@click.group(invoke_without_command=True)
@click.option(
    "--action",
    "-a",
    type=click.Choice(Defaults.ACTIONS, case_sensitive=False),
    default="route",
    help="Choose the action to be performed.",
)
@click.option(
    "--cores",
    "-c",
    type=click.INT,
    default=mp.cpu_count() - 1,
    help="The number of processes to run. Default: all available (virtual) cores minus 1.",
)
@click.option("--version", "-V", is_flag=True, help="Prints version and exit.")
@click.pass_context
def main(ctx: click.Context, action: str, cores: int, version: str) -> None:
    """
    Sets the action and the amount of cores.
    """
    if version and not ctx.invoked_subcommand:
        print(__version__)
        exit(0)

    ctx.obj = {"action": action, "cores": cores}


@main.command(cls=DefaultCommand)
@click.argument("file", type=click.File("r", encoding="utf-8"))
@click.option(
    "--host",
    "-h",
    cls=MutuallyExclusiveOption,
    type=click.STRING,
    help="The OSRM host URL for HTTP.",
    mutually_exclusive=["osrm-file"],
)
@click.option(
    "--osrm-file",
    "-c",
    cls=MutuallyExclusiveOption,
    type=click.Path(exists=True, file_okay=True, readable=True, resolve_path=True),
    help="The OSRM file to be used by the Python bindings.",
    mutually_exclusive=["host"],
)
@click.option(
    "--report",
    "-r",
    is_flag=True,
    type=click.BOOL,
    default=False,
    help="Flag to report the distance average of the routes/matrices.",
)
@click.option(
    "--algorithm",
    "-A",
    cls=MutuallyExclusiveOption,
    type=click.STRING,
    default=Defaults.ALGORITHM,
    help=f"The algorithm that will be used for routing. Only when using bindings. "
    f"Default: {Defaults.ALGORITHM}",
    mutually_exclusive=["host"],
)
@click.pass_context
def test(
    ctx,
    verbosity: int,
    file: TextIOWrapper,
    host: str,
    osrm_file: str,
    report: bool,
    algorithm: str,
) -> None:
    """
    Executes the test either via HTTP ("host" option) or Python bindings.

    Tests requests for each "action" with locations found in "file".
    If a "--departure" time string is given, the routing will be time-dependent.
    If the "--report" flag is set the average distances of the routes/matrices will
    be reported, however, this comes at a performance penalty.
    """
    # set logger level
    level: int = map_verbosity(verbosity)
    LOGGER.setLevel(level)

    if not host and not osrm_file:
        raise click.UsageError("One of (host, osrm-file) is needed.")
    if osrm_file and not OSRM_FOUND:
        raise ModuleNotFoundError("OSRM Python bindings are not installed!")

    cores = ctx.obj["cores"]
    action = ctx.obj["action"]

    reqs = []
    if action == "route":
        for line in file:
            coords: str = literal_eval(line)
            reqs.append(coords)
    elif action == "matrix":
        locs = []
        for line in file:
            coords = literal_eval(line)
            locs.extend([{"lon": x, "lat": y} for x, y in coords])
        reqs.append({"costing": "auto", "sources": locs, "targets": locs})
    else:
        click.UsageError(f"Parameter action must be one of {Defaults.ACTIONS}")

    # lock to open the OSRM file if necessary
    lock = mp.Lock()
    with mp.Pool(
        cores, task_action.init, [action, host, osrm_file, report, algorithm, lock]
    ) as pool:
        start = time.time()
        results = list(
            pool.imap_unordered(task_action.work, reqs, len(reqs) // cores or 1)
        )
        pool.close()
        pool.join()

    end = time.time()

    if report:
        results = list(filter(lambda x: x is not None, results))
        echo_str = f"{str(round(mean(results), 3)) if len(results) > 1 else str(round(results[0], 3))}"  # noqa: E501
        echo_str += " +/- "
        echo_str += str(round(stdev(results), 2)) if len(results) > 1 else "0"
        echo_str += " meters"

        click.secho(f"Average distance of {len(results)} routes/matrices: ", nl=False)
        click.secho(echo_str, fg="bright_blue")

    click.secho("Total time passed: ", nl=False)
    click.secho(str(round(end - start, 2)) + " secs", fg="bright_blue")


@main.command(cls=DefaultCommand)
@click.argument("locations", type=click.INT)
@click.argument("bbox", type=click.STRING)
@click.argument("file", type=click.File("w", encoding="utf-8"))
@click.option(
    "--lower-limit",
    "-l",
    type=click.INT,
    default=Defaults.LOWER_LIMIT,
    help=f"Lower distance limit for 2 waypoints or consecutive locations in meters. "
    f"Default {Defaults.LOWER_LIMIT:,.0f} m.",
)
@click.option(
    "--upper-limit",
    "-u",
    type=click.INT,
    default=Defaults.UPPER_LIMIT,
    help=f"Upper distance limit for 2 waypoints or consecutive locations in meters. "
    f"Default {Defaults.UPPER_LIMIT:,.0f} m.",
)
@click.pass_context
def create_locations(
    ctx,
    verbosity: int,
    locations: int,
    bbox: str,
    file: TextIOWrapper,
    lower_limit: int,
    upper_limit: int,
):
    """
    Creates the locations text file to be read by "osrm_tester test".

    Specify how many "locations" you need for your tests within your "bbox" (format:
    "x_min,y_min,x_max,y_max". It will create pairs of 2 locations with a distance
    of "lower-limit" (default 400 m) < distance < "upper-limit" (default 4000 m).
    """
    level: int = map_verbosity(verbosity)
    LOGGER.setLevel(level)

    action = ctx.obj["action"]
    cores = ctx.obj["cores"]

    # if matrix then half the locations as we always return 2 locations from the worker
    locations = locations // 2 if action == "matrix" else locations
    bbox = [float(x) for x in bbox.split(",")]

    if not bbox_is_valid(bbox):
        click.UsageError(f"Bbox invalid: {bbox}.")

    with mp.Pool(cores, task_locations.init, [bbox, lower_limit, upper_limit]) as pool:
        results = pool.imap_unordered(
            task_locations.work, range(locations), locations // cores or 1
        )
        pool.close()
        pool.join()

    dists = list()
    for result in results:
        if action == "matrix":
            for location in result:
                file.write(str(location) + "\n")
            return
        else:
            dists.append(haversine(*result, unit=Unit.METERS))
            file.write(str(result) + "\n")

    # give some more logging for "route"
    echo_str = (
        f"{str(round(mean(dists), 3)) if len(dists) > 1 else str(round(dists[0], 3))}"
    )
    echo_str += " +/- "
    echo_str += str(round(stdev(dists), 2)) if len(dists) > 1 else "0"
    echo_str += " meters"

    click.secho(f"Average distance of {len(dists)} routes: ", nl=False)
    click.secho(echo_str, fg="bright_blue")
