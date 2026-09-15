"""Command line: plan a site from a JSON scenario.

    python -m cuas plan examples/example.json --out map.png
"""
from __future__ import annotations

import argparse

from . import scenario_io
from .coverage import compute
from .render import render
from .stats import summarise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="cuas", description="C-UAS sensor coverage planner.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="compute and render a scenario")
    p.add_argument("scenario", help="scenario JSON file")
    p.add_argument("--out", default="coverage.png", help="output PNG path")
    p.add_argument("--target-px", type=int, default=820)
    args = ap.parse_args(argv)

    if args.cmd == "plan":
        sc = scenario_io.load(args.scenario)
        result = compute(sc)
        print(summarise(result).as_text())
        out = render(result, args.out, target_px=args.target_px)
        print(f"\nmap written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
