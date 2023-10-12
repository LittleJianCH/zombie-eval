from common import *
import os
from datetime import datetime
import json

import matplotlib.pyplot as plt

programs = ['(elsamuko-national-geographic-batch "picture.jpeg" 60 1 60 25 0.4 1 0)',
            '(gimp-quit 0)']

cwd = os.getcwd()

gimp_program = f"{cwd}/_build/bin/gimp-2.10 -i " + " ".join(["-b " + "\'" + x + "\'" for x in programs])

def timed(f):
    before  = datetime.now()
    f()
    after = datetime.now()
    return (after - before).total_seconds()

os.environ["GEGL_THREADS"] = "1"

def set_zombie(use):
    os.environ["USE_ZOMBIE"] = "1" if use else "0"

def set_zombie_memory(memory):
    os.environ["ZOMBIE_MAX_MEMORY"] = str(memory)

def average_timed():
    times = []
    for i in range(3):
        run(f"cp {cwd}/picture/picture.jpeg ./")
        times.append(timed(lambda: run(gimp_program + "|| true")))

    average_time = sum(times) / len(times)

    sort_list = []
    for t in times:
        sort_list.append([abs(t - average_time), t])
    
    sort_list.sort()

    times = []
    for i in range(2):
        times.append(sort_list[i][1])

    return sum(times) / len(times)

def run_with_config(config, data):
    set_zombie(config["use"])
    set_zombie_memory(config["memory"])

    data[str(config)] = average_timed()

    return data[str(config)]

def run_tests(configs):
    dt = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    log_dir = f"log/{dt}"
    run(f"mkdir -p {log_dir}")
    os.chdir(log_dir)

    export_env_var()

    data = {}

    for cfg in configs:
        run_with_config(cfg, data)

    with open('result.json', 'w') as f:
        json.dump(data, f)
    
    os.chdir(cwd)

    return dt

if __name__ == "__main__":
    configs = [
        {"use": 1, "memory": int(1e5)},
        {"use": 0, "memory": int(1e5)},
    ]

    run_tests(configs)