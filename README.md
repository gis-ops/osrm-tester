# Valhalla tester

CLI tool to test OSRM performance.

## General

**Dependencies**:
- Python >=3.9
- (optional) [Poetry](https://github.com/sdispater/poetry#installation) as package manager

## Installation

Create a virtual environment:
```
python -m venv .venv
source .venv/bin/activate  # or <venv>\Scripts\activate.bat for windows
```

Clone and install locally:

```shell script
git clone git@github.com:gis-ops/osrm-tester.git
cd osrm_tester

poetry install [--no-dev]
```

## Usage

After installation, `osrm_tester --help` can be called from the commandline as executable:

- Linux: `valhalla_tester --help`
- Windows: `.\venv\Scripts\valhalla_tester --help`

```
Usage: osrm_tester [OPTIONS] COMMAND [ARGS]...

  Sets the action and the amount of cores.

Options:
  -a, --action [route|matrix]  Choose the action to be performed.
  -c, --cores INTEGER          The number of processes to run. Default: all
                               available (virtual) cores minus 1.
  -V, --version                Prints version and exit.
  --help                       Show this message and exit.

Commands:
  create-locations  Creates the locations text file to be read by...
  test              Executes the test either via HTTP ("host" option) or...
```

Or, if that's failing for some reason, as a Python script:

```shell script
python -m valhalla_tester --help
```

> **Disclaimer:**
The `matrix` action option is not yet supported.


The options are self-explanatory.

### Commands

#### `create-locations`

This command will create the specified amount of `LOCATIONS` within a `BBOX`.:

```
Usage: osrm_tester create-locations [OPTIONS] LOCATIONS BBOX FILE

  Creates the locations text file to be read by "osrm_tester test".

  Specify how many "locations" you need for your tests within your "bbox"
  (format: "x_min,y_min,x_max,y_max". It will create pairs of 2 locations with
  a distance of "lower-limit" (default 400 m) < distance < "upper-limit"
  (default 4000 m).

Options:
  -v, --verbosity            Accumulative verbosity flags; -v: INFO, -vv:
                             DEBUG, default: CRITICAL
  -l, --lower-limit INTEGER  Lower distance limit for 2 waypoints or
                             consecutive locations in meters. Default 100,000
                             m.
  -u, --upper-limit INTEGER  Upper distance limit for 2 waypoints or
                             consecutive locations in meters. Default
                             1,000,000 m.
  --help                     Show this message and exit.
```

#### `test`

This will actually run the tests and print some statistics to the console.

```
Usage: osrm_tester test [OPTIONS] FILE

  Executes the test either via HTTP ("host" option) or Python bindings.

  Tests requests for each "action" with locations found in "file". If a "--
  departure" time string is given, the routing will be time-dependent. If the
  "--report" flag is set the average distances of the routes/matrices will be
  reported, however, this comes at a performance penalty.

Options:
  -v, --verbosity       Accumulative verbosity flags; -v: INFO, -vv: DEBUG,
                        default: CRITICAL
  -h, --host TEXT       The OSRM host URL for HTTP. NOTE: This argument is
                        mutually exclusive with  arguments: [osrm-file].
  -c, --osrm-file PATH  The OSRM file to be used by the Python bindings. NOTE:
                        This argument is mutually exclusive with  arguments:
                        [host].
  -r, --report          Flag to report the distance average of the
                        routes/matrices.
  --help                Show this message and exit.
```

### Examples

Create a locations file for `route` action with 20 routes in Vienna:

```shell script
osrm_tester create-locations 20 16.29960159,48.15989365,16.48595972,48.25247813 ./test_vienna.txt
```

Run tests for the above file for `route` action and HTTP requests time to use historical traffic:

```shell script
osrm_tester test --host http://localhost:5000 ./test_vienna.txt
```

Run tests for the above file for `route` action and Python bindings:

```shell script
osrm_tester test --osrm-file ./vienna.osrm ./test_vienna.txt
```
