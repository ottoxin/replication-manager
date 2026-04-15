from __future__ import annotations

import argparse

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replication-manager",
        description="Run a simplified replication workflow on a paper and replication package.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the replication workflow.")
    run_parser.add_argument("--paper", required=True, help="Paper path or URL.")
    run_parser.add_argument("--package", required=True, help="Replication package path, directory, or URL.")
    run_parser.add_argument("--output-dir", required=True, help="Directory for run outputs.")
    run_parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Run directly in the unpacked workspace instead of a clean copied sandbox.",
    )
    run_parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip dependency bootstrap inside the sandbox.",
    )
    run_parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Do not execute scripts; only inspect artifacts already present in the package.",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=600,
        help="Per-script timeout in seconds.",
    )
    run_parser.add_argument(
        "--stata-bin",
        default=None,
        help="Override the Stata binary path for .do execution.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        result = run_pipeline(
            paper_source=args.paper,
            package_source=args.package,
            output_dir=args.output_dir,
            execute=not args.no_execute,
            sandbox=not args.no_sandbox,
            install_dependencies=not args.no_install,
            timeout_seconds=args.timeout_seconds,
            stata_bin=args.stata_bin,
        )
        summary = result.comparison.summary
        print(f"Verdict: {summary.verdict}")
        print(
            f"Sandbox: {'enabled' if result.sandbox_manifest.enabled else 'disabled'} "
            f"with {len(result.sandbox_manifest.install_records)} bootstrap step(s)"
        )
        print(
            "Match rates: "
            f"numbers={summary.numeric_match_rate:.1%}, "
            f"tables={summary.table_match_rate:.1%}, "
            f"figures={summary.figure_match_rate:.1%}"
        )
        print(f"Markdown report: {result.report_markdown}")
        print(f"HTML report: {result.report_html}")


if __name__ == "__main__":
    main()
