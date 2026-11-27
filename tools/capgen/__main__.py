"""Generate a capability scaffold from a JSON definition."""

from argparse import ArgumentParser
from pathlib import Path

from tools.capgen.generator import generate


def main() -> None:
    """Parse a definition file and write the layout to the given directory."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("definition", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    generate(arguments.definition, arguments.output)


if __name__ == "__main__":
    main()
