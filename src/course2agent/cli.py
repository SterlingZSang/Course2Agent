from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import build_course
from .runtime import CourseIndex, serve, self_test


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="course2agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build a course-agent package")
    build.add_argument("sources", nargs="+", help="Course files or directories")
    build.add_argument("--output", required=True)
    build.add_argument("--title")
    build.add_argument("--slug")

    search = subparsers.add_parser("search", help="Search a built course package")
    search.add_argument("root")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--role")

    inspect = subparsers.add_parser("inspect", help="Show package coverage")
    inspect.add_argument("root")

    check = subparsers.add_parser("verify", help="Run package self-test")
    check.add_argument("root")

    server = subparsers.add_parser("serve", help="Start the stdio MCP server")
    server.add_argument("root")
    return parser


def main() -> None:
    args = make_parser().parse_args()
    if args.command == "build":
        output = build_course(args.sources, args.output, args.title, args.slug)
        print(output)
    elif args.command == "search":
        value = CourseIndex(args.root).search(args.query, args.limit, args.role)
        print(json.dumps(value, ensure_ascii=False, indent=2))
    elif args.command == "inspect":
        print(json.dumps(CourseIndex(args.root).overview(), ensure_ascii=False, indent=2))
    elif args.command == "verify":
        report = self_test(Path(args.root))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report["ok"] else 1)
    elif args.command == "serve":
        serve(args.root)


if __name__ == "__main__":
    main()

