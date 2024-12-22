# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tomli-w",
# ]
# ///
import re

import tomli_w
import tomllib

pyproject = "pyproject.toml"

pattern = re.compile(r"^([a-zA-Z0-9._-]+)(?:\[(.*)\])?(==|>=|<=|~=|!=|<|>)?([\d.]+)?$")

with open("requirements.txt", "r") as f:
    lines = f.read().splitlines()

deps = {}
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    match = pattern.match(line)
    if match:
        name = match.group(1)
        extras = match.group(2)
        operator = match.group(3) or ""
        version = match.group(4) or "*"
        if extras:
            deps[name] = {
                "version": operator + version if operator else version,
                "extras": [e.strip() for e in extras.split(",")],
            }
        else:
            deps[name] = operator + version if operator else version

with open(pyproject, "rb") as f:
    py = tomllib.load(f)

py["tool"]["poetry"]["dependencies"].update(deps)

with open(pyproject, "wb") as f:
    tomli_w.dump(py, f)
