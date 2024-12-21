# /// script
# requires-python = ">=3.12"
# dependencies = [
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
NUM_ITER = "1"
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
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.clean_cache}",
                "prepare": "",
                "target": self._tool.lock,
                "conclude": f"{self._tool.clean_lock} && {self._tool.clean_venv} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def install(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.lock} && {self._tool.clean_cache}",
                "prepare": "",
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
                "prepare": f"{self._tool.install} && {clean_cache}",
                "target": self._tool.update,
                "conclude": f"{self._tool.clean_venv} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def add(self, cache: bool = False) -> CMD:
        clean_cache = "true" if cache else self._tool.clean_cache
        return CMD(
            **{
                "setup": f"{self._tool.setup} && {self._tool.install_tool} && {self._tool.import_dependency} && {self._tool.install} && cp pyproject.toml{{,.bak}} && cp {self._tool.lock_file}{{,.bak}}",
                "prepare": f"{self._tool.install} && {clean_cache}",
                "target": self._tool.add,
                "conclude": f"{self._tool.clean_venv} && cp pyproject.toml{{.bak,}} && cp {self._tool.lock_file}{{.bak,}} && {clean_cache}",
                "cleanup": f"{self._tool.uninstall_tool} && {self._tool.cleanup}",
            }
        )

    def version(self) -> CMD:
        return CMD(
            **{
                "setup": self._tool.setup,
                "prepare": "",
                "target": self._tool.version,
                "conclude": "",
                "cleanup": self._tool.cleanup,
            }
        )


class Uv:
    name: str = "uv"
    clean_introduce_cache: str = "true"
    clean_cache: str = "rm -rf .cache"
    clean_venv: str = "rm -rf .venv"
    clean_lock: str = "rm uv.lock"
    install_tool: str = (
        'curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="./bin/" sh'
    )
    uninstall_tool: str = "rm -r bin"
    setup: str = "true"
    cleanup: str = "true"
    lock_file: str = "uv.lock"
    import_dependency: str = "bin/uv add --frozen -r requirements.txt"
    # tool command
    lock: str = "bin/uv lock"
    install: str = "bin/uv sync"
    update: str = "bin/uv sync --upgrade"
    add: str = f"bin/uv add {ADD_PACKAGE}"
    version: str = "uv --version | awk '{print $2}'"


class Poetry:
    name: str = "poetry"
    clean_cache: str = "rm -rf ~/.cache/pypoetry"
    clean_introduce_cache: str = "rm -rf ~/.local/pipx"
    clean_venv: str = "rm -r .venv"
    setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
    cleanup: str = "uv tool uninstall pipx"
    install_tool: str = "uvx pipx install poetry"
    uninstall_tool: str = "uvx pipx uninstall poetry"
    clean_lock: str = "rm -rf poetry.lock"
    lock_file: str = "poetry.lock"
    import_dependency: str = "uv run --no-project import_dependency.py"
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
    clean_venv: str = "rm -r .venv"
    setup: str = f"uv tool install --python {PYTHON_VERSION} pipx"
    cleanup: str = "uv tool uninstall pipx"
    install_tool: str = "uvx pipx install pdm"
    uninstall_tool: str = "uvx pipx uninstall pdm"
    clean_lock: str = "rm -rf pdm.lock"
    lock_file: str = "pdm.lock"
    import_dependency: str = "pdm import -f requirements requirements.txt"
    # tool command
    lock: str = "pdm lock"
    install: str = "pdm install"
    update: str = "pdm update"
    add: str = f"pdm add {ADD_PACKAGE}"
    version: str = "pdm --version | awk '{print $3}'"


def command_factory(tool: str, method: str, cache: bool) -> CMD:
    if tool == "poetry":
        tool = Poetry()
    elif tool == "uv":
        tool = Uv()
    elif tool == "pdm":
        tool = Pdm()

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


class Args(BaseModel):
    """Script argument."""

    tool: Literal["uv", "poetry", "pdm"]
    method: Literal["introduce", "lock", "install", "update", "add"]
    cache: bool


@click.command()
@from_pydantic(Args)
def cli(args: Args) -> None:
    cmd = command_factory(args.tool, args.method, args.cache)
    import os
    import shutil

    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copy("requirements.txt", temp_dir)

        if os.path.exists(args.tool):
            for item in os.listdir(args.tool):
                src_path = os.path.join(args.tool, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, f"{temp_dir}/{item}")
                else:
                    shutil.copy2(src_path, f"{temp_dir}/{item}")

        del os.environ["VIRTUAL_ENV"]
        subprocess.run(
            [
                "hyperfine",
                "--show-output",
                "--export-csv",
                "stats.csv",
                "--runs",
                NUM_ITER,
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
                os.environ,
            ]
            + (["--warmup", "1"] if args.cache else []),
            check=True,
            cwd=temp_dir,
        )

        # get version
        cmd = command_factory(args.tool, "version", args.cache)
        version = subprocess.run(
            [
                f"{cmd.setup} > /dev/null 2>&1 && {cmd.target} && {cmd.cleanup} > /dev/null 2>&1"
            ],
            shell=True,
            capture_output=True,
            text=True,
            cwd=temp_dir,
        ).stdout.strip()

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
                # stats.csv が存在しない場合は丸ごとコピー
                with open(destination_file, "w", encoding="utf-8", newline="") as dest:
                    writer = csv.writer(dest)
                    header = rows[0]
                    del header[0]
                    header = ["tool", "version", "method", "cache"] + header
                    writer.writerows([header] + data_rows)


if __name__ == "__main__":
    cli()
