# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pydanclick",
#     "pydantic",
# ]
# ///
import csv

import click
from pydanclick import from_pydantic
from pydantic import BaseModel

THIRD_COLUMN_ORDER = ["introduce", "lock", "install", "update", "add"]
FOURTH_COLUMN_ORDER = [False, True]


class Args(BaseModel):
    input_file: str
    output_file: str | None = None


@click.command()
@from_pydantic(Args, shorten={"input_file": "-i", "output_file": "-o"})
def cli(args: Args):
    if args.output_file is None:
        args.output_file = args.input_file

    with open(args.input_file, mode="r", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader)

    for row in rows:
        for i in range(4, len(row)):
            row[i] = f"{float(row[i]):.4f}"

    rows.sort(
        key=lambda x: (
            x[0],
            THIRD_COLUMN_ORDER.index(x[2]),
            FOURTH_COLUMN_ORDER.index(x[3] == "True"),
        )
    )

    with open(args.output_file, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(rows)


if __name__ == "__main__":
    cli()
