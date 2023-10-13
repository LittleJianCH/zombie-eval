import json
import os
from eval import *
from common import *
from os import sys
import dominate
from dominate.tags import *
import matplotlib.pyplot as plt

class page(dominate.document):
    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path

    def _add_to_ctx(self):
        pass # don't add to contexts

    def __exit__(self, *args):
        super().__exit__(*args)
        with open(str(self.path), "w") as f:
            f.write(str(self))

def gen_chart(configs, data):
    fig, ax = plt.subplots()

    baseline_x = []
    baseline_y = []
    zombie_x = []
    zombie_y = []
    for config in configs:
        value = data[config]
        if config["use"] == 0:
            baseline_x.appned(config["memory"])
            baseline_y.append(value)
        else:
            zombie_x.append(config["memory"])
            zombie_y.append(value)
    
    ax.plot(baseline_x, baseline_y, label='Baseline', color='red')
    ax.plot(zombie_x, zombie_y, label='Zombie', color='goldenrod')

    ax.legend()

    plt.savefig("chart.png")
    plt.show()

def nightly(dry):
    cwd = os.getcwd()

    configs = [
        {"use": 1, "memory": int(1e5)},
        {"use": 1, "memory": int(1e6)},
        {"use": 1, "memory": int(5e6)},
        {"use": 1, "memory": int(1e7)},
        {"use": 0, "memory": int(1e5)},
        {"use": 0, "memory": int(1e7)},
    ]

    dt = run_tests(configs)

    out_dir = f"{cwd}/out"
    out_dir_dt = f"{cwd}/out/{dt}"

    log_dir = f"{cwd}/log"
    log_dir_dt = f"{cwd}/log/{dt}"

    with open(f'{log_dir_dt}/result.json') as f:
        data = json.load(f)

    run(f"mkdir -p {out_dir_dt}")
    os.chdir(out_dir_dt)

    with page(path=f"index.html", title="nightly") as doc:
        for cfg in configs:
            p(f"{cfg} = {data[str(cfg)]}")

        gen_chart(configs, data)
        img(src="chart.png")

    os.chdir(out_dir)

    if dry:
        run(f"xdg-open {dt}/index.html")
    else:
        run(f"nightly-results publish {dt}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        assert sys.argv[1] == "dry-run"
        nightly(dry=True)
    else:
        assert len(sys.argv) == 1
        nightly(dry=False)
