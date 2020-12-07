from contextlib import contextmanager
from typing import Iterator

import gurobipy as grb

SERVER = "kl134fy5.is.klmcorp.net:8000"
LICENSE = "Gurobi-AE"
STDERR = "/dev/stderr"


@contextmanager
def model(name: str) -> Iterator[grb.Model]:
    with grb.Env.ClientEnv("", SERVER, password=LICENSE) as env:
        env.setParam("LogToConsole", False)
        with grb.Model(name, env) as model:
            model.setParam("LogFile", STDERR)
            yield model
