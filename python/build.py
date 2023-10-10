from pathlib import Path
import os
import subprocess
from common import *
import sys
import getpass

IS_NIGHTLY = False
if IS_NIGHTLY:
    USERNAME = "littlejian"
else:
    USERNAME = getpass.getuser()

DEBUG = True

def build_type():
    return "debug" if DEBUG else "release"

class Module:
    def __init__(self, name, dependency):
        self.name = name
        os.chdir(third_party_dir)
        self.path = Path(self.name).resolve()
        self.build_path = Path(self.name + "/_build").resolve()
        self.build_ok_path = Path(self.name + "/_build/ok").resolve()
        self.dependency = dependency

        self.dependent = []

        for m in self.dependency:
            m.dependent.append(self)

    def pull(self):
        def worker(m, x):
            os.chdir(third_party_dir)
            if not m.path.exists():
                run(f"git clone 'git@github.com:MarisaKirisame/{m.name}.git'")
            os.chdir(m.path)
            run(f"git pull origin {USERNAME} || true")
            run(f"git checkout {USERNAME} || git checkout -b {USERNAME}")

        self.recurse(worker)

    def cloned(self):
        def worker(m, x):
            os.chdir(third_party_dir)
            return m.path.exists() and all(x)

        return self.recurse(worker)

    def build_impl(self):
        raise NotImplementedError

    def is_dirty(self):
        os.chdir(self.path)
        return not (self.build_ok_path.exists() and query("git rev-parse HEAD") == query("cat '_build/ok'"))

    def dirty(self):
        os.chdir(self.path)
        build_ok = Path("_build/ok")
        if build_ok.exists():
            run("rm '_build/ok'")
        assert self.is_dirty()

    def clean(self):
        assert self.is_dirty()
        os.chdir(self.path)
        run("git rev-parse HEAD > '_build/ok'")
        assert not self.is_dirty()

    # cycle should not exist because dependency is a constructor parameter
    def recurse(self, f, visited=None):
        if visited is None:
            visited = {}
        if self not in visited:
            for m in self.dependency:
                m.recurse(f, visited)
            visited[self] = f(self, [visited[m] for m in self.dependency])
        return visited[self]

    def save(self):
        def worker(m, x):
            os.chdir(third_party_dir)
            os.chdir(m.path)
            run("git commit -am 'save' || true")
            if query("git status --porcelain") != "":
                print(query("git status --porcelain"))
                print("Git repo dirty. Quit.")
                raise

        self.recurse(worker)

    def push(self):
        def worker(m, x):
            os.chdir(third_party_dir)
            os.chdir(m.path)
            # run(f"git push --set-upstream origin {USERNAME} || true")

        self.recurse(worker)

    # return whether any work is done
    def build(self):
        def worker(m, x):
            if any(x):
                m.dirty()
            if m.is_dirty():
                print(f"building {m.name} as it is not clean...")
                os.chdir(m.path)
                m.build_impl()
                m.clean()
                print(f"{m.name} build ok!")
                return True
            else:
                return False

        return self.recurse(worker)

class Zombie(Module):
    def __init__(self):
        super().__init__("zombie", [])

    def build_impl(self):
        if not Path("_build").exists():
            run("mkdir _build")
            os.chdir("_build")
            run(f"cmake -DCMAKE_INSTALL_PREFIX={install_dir} ../")
        os.chdir(self.build_path)
        run(f"make install")

class Babl(Module):
    def __init__(self):
        super().__init__("babl", [])

    def build_impl(self):
        if not Path("_build").exists():
            run(f"meson _build --prefix={install_dir} --buildtype=debug -Db_lto=true")
            run("meson configure _build -Denable-gir=true")
        run("ninja -C _build install")

class Gegl(Module):
    def __init__(self):
        super().__init__("gegl", [babl, zombie])

    def build_impl(self):
        if not Path("_build").exists():
            run(f"meson _build --prefix={install_dir} --buildtype={build_type()} -Db_lto=true")
        run("ninja -C _build install")

class Gimp(Module):
    def __init__(self):
        super().__init__("gimp", [gegl])

    def build_impl(self):
        if not Path("_build").exists():
            run("mkdir _build")
            os.chdir("_build")
            run(f"../autogen.sh --prefix={install_dir} --disable-python")
        os.chdir(self.build_path)
        run("make install")
        os.chdir(zombie_eval_dir)
        run("cp scripts/* _build/share/gimp/2.0/scripts")

zombie = Zombie()
babl = Babl()
gegl = Gegl()
gimp = Gimp()

def build():
    export_env_var()
    gimp.save()
    gimp.build()
    gimp.push()

def setup():
    export_env_var()
    gimp.pull()
    gimp.save()
    gimp.build()
    gimp.push()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        if gimp.cloned():
            build()
        else:
            setup()
    else:
        assert len(sys.argv) == 2
        assert sys.argv[1] == "nightly"
        IS_NIGHTLY = True
        setup()
