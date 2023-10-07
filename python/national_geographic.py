from common import *
import os
from datetime import datetime
import json

import matplotlib.pyplot as plt

programs = ['(elsamuko-national-geographic-batch "picture.jpeg" 60 1 60 25 0.4 1 0)',
            '(gimp-quit 0)']

DEBUG = False

cwd = os.getcwd()

gimp_program = f"{cwd}/_build/bin/gimp-2.10 -i " + " ".join(["-b " + "\'" + x + "\'" for x in programs])

if DEBUG:
    gimp_program = f"gdb -return-child-result -ex='set confirm on' -ex=run -ex=quit --args {gimp_program}"
    #gimp_program = f"valgrind {gimp_program}"

def timed(f):
    before  = datetime.now()
    f()
    after = datetime.now()
    return (after - before).total_seconds()

os.environ["GEGL_THREADS"] = "1"

def set_zombie(use):
    os.environ["USE_ZOMBIE"] = "1" if use else "0"

def set_zombie_score(score = 0):
    os.environ["ZOMBIE_MAX_SCORE"] = str(score)

def set_zombie_memory(memory = 0):
    os.environ["ZOMBIE_MAX_MEMORY"] = str(memory)

def use_zombie():
    set_zombie(True)

def unuse_zombie():
    set_zombie(False)

def run_single_eval(name, data):
    run(f"cp {cwd}/picture/picture.jpeg ./")
    # we are measuring end to end time instead of cpu time,
    # because when it is swapping cpu is idling.
    used_time = timed(lambda: run(gimp_program + "|| true"))

    print(f"running {name} take {used_time}")
    data[f"{name}_used_time"] = used_time
    run(f"mv picture.jpeg {name}.jpeg")

def run_multi_eval():
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

def draw_pic(): 
    print('start drawing pic')
    zombie_times = []
    baseline_times = []
    differents = []
    x = []

    times = 5

    raw_data = []

    # memories = [927686448, 1027686448, 1427686448]
    memory = 1427686448
    gap = int((1427686448 - 1900000) / (times - 1))
    eviction_count = []
    recompute = []
    for _ in range(times):
        x.append(memory)
        
        # when there's no recompute, recompute.log won't be created
        with open("recompute.log", "w") as f:
            f.write("0\n")

        set_zombie_memory(memory)
        unuse_zombie()
        baselineT = run_multi_eval()
        baseline_times.append(baselineT)

        use_zombie()
        zombieT = run_multi_eval()
        zombie_times.append(zombieT)

        raw_data.append((memory, zombieT))

        differents.append(zombieT - baselineT)

        with open("evction_count.log", "r") as f:
            eviction_count.append(int(f.readline()))
        
        with open("recompute.log", "r") as f:
            recompute.append(int(f.readline()))

        memory = memory - gap
    
    fig, ax = plt.subplots()
    bx = ax.twinx()
    cx = ax.twinx()

    ax.plot(x, baseline_times, label='Baseline', color='red')
    ax.plot(x, zombie_times, label='Zombie', color='goldenrod')
    ax.plot(x, differents, label='Different', color='green')
    bx.plot(x, eviction_count, label='Eviction Count', color='dimgrey')
    cx.plot(x, recompute, label="Recompute", color='blue')

    ax.legend()
    bx.legend()

    plt.savefig("pic.png")
    plt.show()

    with open("raw_data.log", "w") as f:
        f.write(str(raw_data))

def ng():
    dt = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    log_dir = f"log/{dt}"
    run(f"mkdir -p {log_dir}")
    os.chdir(log_dir)

    export_env_var()

    data = {}

    set_zombie_score(18438684064490847880)
    set_zombie_memory(int(5e6))

    unuse_zombie()
    run_single_eval("baseline", data)

    use_zombie()
    run_single_eval("zombie", data)

    data["diff"] = float(query("compare -metric phash baseline.jpeg zombie.jpeg delta.jpeg 2>&1 || true"))

    run(f"cp {cwd}/picture/picture.jpeg ./original.jpeg")

    with open('result.json', 'w') as f:
        json.dump(data, f)

    os.chdir(cwd)

    print(f"eval log written to {log_dir}")

    draw_pic()

    return dt

if __name__ == "__main__":
    ng()
