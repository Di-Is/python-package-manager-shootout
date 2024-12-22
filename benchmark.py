# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "pydanclick",
#     "pydantic",
# ]
# ///
import csv
import subprocess
import tempfile
from typing import Literal

import click
from pydanclick import from_pydantic
from pydantic import BaseModel

PYTHON_VERSION = "3.9"
ADD_PACKAGE = "goodconf"


class CMD(BaseModel):
    setup: str
    prepare: str
    target: str
    conclude: str
    cleanup: str


class ModernBenchmarkCMD:
    def __init__(self, tool):
        self._tool: Poetry = tool

    def introduce(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_introduce_cache
        return CMD(
            **{
                "setup": self._tool.setup,
                "prepare": "",
                "target": self._tool.install_tool,
                "conclude": f"{self._tool.uninstall_tool} && {clean_cache}",
                "cleanup": self._tool.cleanup,
            }
        )

    def lock(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.clean_lock} && {self._tool.clean_cache}",
                "prepare": self._tool.create_venv,
                "target": self._tool.lock,
                "conclude": f"{self._tool.clean_lock} && {self._tool.clean_venv} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def install(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.lock} && {self._tool.clean_venv} && {self._tool.clean_cache}",
                "prepare": self._tool.create_venv,
                "target": self._tool.install,
                "conclude": f"{self._tool.clean_venv} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def update(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency}",
                "prepare": f"{self._tool.create_venv} && {self._tool.install} && {clean_cache}",
                "target": self._tool.update,
                "conclude": f"{self._tool.clean_venv} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def add(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.install} && cp {self._tool.pkg_file}{{,.bak}} && cp {self._tool.lock_file}{{,.bak}}",
                "prepare": f"{self._tool.create_venv} && {self._tool.install} && {clean_cache}",
                "target": self._tool.add,
                "conclude": f"{self._tool.clean_venv} && cp {self._tool.pkg_file}{{.bak,}} && cp {self._tool.lock_file}{{.bak,}} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def version(self) -> CMD:
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool}",
                "prepare": self._tool.create_venv,
                "target": self._tool.version,
                "conclude": self._tool.clean_venv,
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )


class Tool:
    name: str


class Uv:
    name: str = "uv"
    clean_introduce_cache: str = "true"
    clean_cache: str = "rm -rf .cache"
    clean_venv: str = "rm -rf .venv"
    clean_lock: str = "rm -rf uv.lock"
    install_tool: str = (
        'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="./bin/" sh'
    )
    uninstall_tool: str = "rm -r bin"
    create_venv: str = "true"
    setup: str = "true"
    cleanup: str = "true"
    lock_file: str = "uv.lock"
    pkg_file: str = "pyproject.toml"
    import_dependency: str = "bin/uv add --frozen -r requirements.txt"
    envs = {}
    # tool command
    lock: str = "bin/uv lock"
    install: str = "bin/uv sync"
    update: str = "bin/uv sync --upgrade"
    add: str = f"bin/uv add {ADD_PACKAGE}"
    version: str = "bin/uv --version | awk '{print $2}'"


class Poetry:
    name: str = "poetry"
    clean_cache: str = "rm -rf .cache"
    clean_introduce_cache: str = "rm -rf ~/.local/pipx"
    clean_venv: str = "rm -rf .venv"
    setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
    cleanup: str = "uv tool uninstall pipx"
    install_tool: str = "uvx pipx install poetry"
    uninstall_tool: str = "uvx pipx uninstall poetry"
    create_venv: str = "true"
    clean_lock: str = "rm -rf poetry.lock"
    lock_file: str = "poetry.lock"
    pkg_file: str = "pyproject.toml"
    import_dependency: str = "uv run --no-project import_dependency.py"
    envs = {}
    # tool command
    lock: str = "poetry lock"
    install: str = "poetry install"
    update: str = "poetry update"
    add: str = f"poetry add '{ADD_PACKAGE}=*'"
    version: str = "poetry --version | awk '{print $3}' | tr -d ')'"


class Pdm:
    name: str = "pdm"
    clean_cache: str = "rm -rf ~/.cache/pdm"
    clean_introduce_cache: str = "rm -rf ~/.local/pipx"
    clean_venv: str = "rm -rf .venv"
    setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
    cleanup: str = "uv tool uninstall pipx"
    install_tool: str = "uvx pipx install pdm"
    uninstall_tool: str = "uvx pipx uninstall pdm"
    create_venv: str = "true"
    clean_lock: str = "rm -rf pdm.lock"
    lock_file: str = "pdm.lock"
    pkg_file: str = "pyproject.toml"
    import_dependency: str = "pdm import -f requirements requirements.txt"
    envs = {}
    # tool command
    lock: str = "pdm lock"
    install: str = "pdm install"
    update: str = "pdm update"
    add: str = f"pdm add {ADD_PACKAGE}"
    version: str = "pdm --version | awk '{print $3}'"


class Pipenv:
    name: str = "pipenv"
    clean_cache: str = "rm -rf /tmp/.cache/pipenv"
    clean_introduce_cache: str = "rm -rf ~/.local/pipx"
    clean_venv: str = "rm -rf .venv"
    setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
    cleanup: str = "uv tool uninstall pipx"
    install_tool: str = "uvx pipx install pipenv"
    uninstall_tool: str = "uvx pipx uninstall pipenv"
    clean_lock: str = "rm -rf Pipfile.lock"
    create_venv: str = "true"
    pkg_file: str = "Pipfile"
    lock_file: str = "Pipfile.lock"
    import_dependency: str = "pipenv install -r requirements.txt"
    envs: dict = {
        "PIPENV_VENV_IN_PROJECT": "true",
        "PIPENV_CACHE_DIR": "/tmp/.cache/pipenv",
    }
    # tool command
    lock: str = "pipenv lock"
    install: str = "pipenv sync"
    update: str = "pipenv update"
    add: str = f"pipenv install {ADD_PACKAGE}"
    version: str = "pipenv --version | awk '{print $3}'"


class UvPip:
    name: str = "uv-pip"
    clean_introduce_cache: str = "true"
    clean_cache: str = "rm -rf .cache"
    clean_venv: str = "rm -rf .venv"
    clean_lock: str = "true"
    install_tool: str = (
        'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="./bin/" sh'
    )
    uninstall_tool: str = "rm -r bin"
    create_venv: str = "uv venv"
    setup: str = "true"
    cleanup: str = "true"
    lock_file: str = "requirements.txt"
    pkg_file: str = "requirements.txt"
    import_dependency: str = "true"
    envs = {"UV_CACHE_DIR": ".cache"}
    # tool command
    lock: str = "true"
    install: str = "bin/uv pip install -r requirements.txt"
    update: str = "true"
    add: str = "true"
    version: str = "bin/uv --version | awk '{print $2}'"


class Pip:
    name: str = "pip"
    clean_introduce_cache: str = "true"
    clean_cache: str = "rm -rf .cache"
    clean_venv: str = "rm -rf .venv"
    clean_lock: str = "true"
    install_tool: str = (
        'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="./bin/" sh'
    )
    uninstall_tool: str = "rm -r bin"
    create_venv: str = "uv venv && uv pip install pip"
    setup: str = "true"
    cleanup: str = "true"
    lock_file: str = "requirements.txt"
    pkg_file: str = "requirements.txt"
    import_dependency: str = "true"
    envs = {"PIP_CACHE_DIR": ".cache"}
    # tool command
    lock: str = "true"
    install: str = ".venv/bin/pip install -r requirements.txt"
    update: str = "true"
    add: str = "true"
    version: str = ".venv/bin/pip --version | awk '{print $2}'"


# class Piptools:
#     name: str = "pip-tools"
#     clean_cache: str = "rm -rf /tmp/.cache/piptools"
#     clean_introduce_cache: str = "rm -rf ~/.local/pipx"
#     clean_venv: str = "rm -rf .venv"
#     setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
#     cleanup: str = "uv tool uninstall pipx"
#     create_venv: str = "true"
#     install_tool: str = "uvx pipx install pip-tools"
#     uninstall_tool: str = "uvx pipx uninstall pip-tools"
#     clean_lock: str = "rm -rf requirements.lock"
#     pkg_file: str = "requirements.lock"
#     lock_file: str = "requirements.lock"
#     import_dependency: str = "pipenv install -r requirements.lock"
#     envs: dict = {
#         "PIP_TOOLS_CACHE_DIR": "/tmp/.cache/piptools",
#     }
#     # tool command
#     lock: str = "pip-compile --generate-hashes --resolver=backtracking --output-file=requirements.lock requirements.txt"
#     install: str = "pip-sync --python-executable=.venv/bin/python --pip-args '--no-deps' pip-tools/requirements.txt"
#     update: str = "pipenv update"
#     add: str = f"pipenv install {ADD_PACKAGE}"
#     version: str = "pipenv --version | awk '{print $3}'"


def command_factory(tool: str, method: str, cache: bool) -> CMD:
    if tool == "poetry":
        tool = Poetry()
    elif tool == "uv":
        tool = Uv()
    elif tool == "pdm":
        tool = Pdm()
    elif tool == "pipenv":
        tool = Pipenv()
    elif tool == "uv-pip":
        tool = UvPip()
    elif tool == "pip":
        tool = Pip()

    cmder = ModernBenchmarkCMD(tool)

    if method == "introduce":
        cmd = cmder.introduce(cache)
    elif method == "lock":
        cmd = cmder.lock(cache)
    elif method == "install":
        cmd = cmder.install(cache)
    elif method == "update":
        cmd = cmder.update(cache)
    elif method == "add":
        cmd = cmder.add(cache)
    elif method == "version":
        cmd = cmder.version()

    return cmd


def env_factory(tool: str) -> dict:
    if tool == "poetry":
        tool = Poetry()
    elif tool == "uv":
        tool = Uv()
    elif tool == "pdm":
        tool = Pdm()
    elif tool == "pipenv":
        tool = Pipenv()
    elif tool == "uv-pip":
        tool = UvPip()
    elif tool == "pip":
        tool = Pip()
    return tool.envs


class Args(BaseModel):
    """Script argument."""

    tool: Literal["uv", "poetry", "pdm", "pipenv", "uv-pip", "pip"]
    method: Literal["introduce", "lock", "install", "update", "add"]
    num_iter: int = 5
    output_file: str = "stats.csv"
    cache: bool


@click.command()
@from_pydantic(
    Args,
    shorten={"tool": "-t", "method": "-m", "num_iter": "-n", "output_file": "-o"},
)
def cli(args: Args) -> None:
    cmd = command_factory(args.tool, args.method, args.cache)
    tool_envs = env_factory(args.tool)
    import os
    import shutil

    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copy("requirements.txt", temp_dir)
        tool_dir = f"package/{args.tool}"
        if os.path.exists(tool_dir):
            for item in os.listdir(tool_dir):
                src_path = os.path.join(tool_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, f"{temp_dir}/{item}")
                else:
                    shutil.copy2(src_path, f"{temp_dir}/{item}")

        envs = os.environ.copy()
        if "VIRTUAL_ENV" in envs:
            del envs["VIRTUAL_ENV"]
        if "UV_CACHE_DIR" in envs:
            del envs["UV_CACHE_DIR"]
        if "/archive-v0/" in envs["PATH"]:
            envs["PATH"] = ":".join(
                [item for item in envs["PATH"].split(":") if "/archive-v0/" not in item]
            )
        envs |= tool_envs
        print(envs)
        subprocess.run(
            [
                "hyperfine",
                "--show-output",
                "--export-csv",
                args.output_file,
                "--runs",
                f"{args.num_iter}",
                "--setup",
                cmd.setup,
                "--prepare",
                cmd.prepare,
                "--conclude",
                cmd.conclude,
                "--cleanup",
                cmd.cleanup,
                cmd.target,
                "--shell",
                "bash",
            ]
            + (["--warmup", "1"] if args.cache else []),
            check=True,
            cwd=temp_dir,
            env=envs,
        )

        # get version
        cmd = command_factory(args.tool, "version", args.cache)
        subprocess.run(cmd.setup, shell=True, cwd=temp_dir)
        version = subprocess.run(
            cmd.target,
            capture_output=True,
            cwd=temp_dir,
            text=True,
            shell=True,
            check=True,
        ).stdout.strip()
        subprocess.run(cmd.cleanup, shell=True, cwd=temp_dir)

        with open(f"{temp_dir}/stats.csv", "r", encoding="utf-8") as src:
            reader = csv.reader(src)
            rows = list(reader)

            if not rows:
                print("Source file is empty.")
                return

            # replace command name
            data_rows = rows[1:]
            del data_rows[0][0]
            data_rows[0] = [args.tool, version, args.method, args.cache] + data_rows[0]

            destination_file = "stats.csv"
            if os.path.exists(destination_file):
                with open(destination_file, "a", encoding="utf-8", newline="") as dest:
                    writer = csv.writer(dest)
                    writer.writerows(data_rows)
            else:
                with open(destination_file, "w", encoding="utf-8", newline="") as dest:
                    writer = csv.writer(dest)
                    header = rows[0]
                    del header[0]
                    header = ["tool", "version", "method", "cache"] + header
                    writer.writerows([header] + data_rows)


if __name__ == "__main__":
    cli()
