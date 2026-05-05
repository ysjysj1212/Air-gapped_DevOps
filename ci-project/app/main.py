"""Entry point for the ci-project CLI."""

import argparse
import sys

from app.ci_generator import generate
from app.ci_runner import run
from app.parser import parse_pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate and optionally run a CI pipeline"
    )
    parser.add_argument("language", help="Target language (python, nodejs, java, go)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the generated pipeline locally",
    )
    parser.add_argument(
        "--workdir",
        default=".",
        help="Working directory for pipeline execution (default: .)",
    )

    args = parser.parse_args(argv)

    pipeline_yaml = generate(args.language)
    metadata = parse_pipeline(pipeline_yaml)

    print("=== Generated CI Pipeline ===")
    print(pipeline_yaml)
    print(f"\nDetected language: {metadata['language']}")
    print(f"Stages: {metadata['stages']}")
    print(f"Jobs: {metadata['jobs']}")

    if args.run:
        print("\n=== Running Pipeline ===")
        result = run(pipeline_yaml, workdir=args.workdir)
        print(result["output"])
        sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
