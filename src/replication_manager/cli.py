from __future__ import annotations

import argparse

from .log import set_level
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="replication-manager",
        description="Run a replication workflow on a paper and replication package.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the replication workflow.")
    run_parser.add_argument("--paper", required=True, help="Paper path or URL.")
    run_parser.add_argument("--package", required=True, help="Replication package path, directory, or URL.")
    run_parser.add_argument("--output-dir", required=True, help="Directory for run outputs.")
    run_parser.add_argument("--no-sandbox", action="store_true", help="Run directly without sandbox isolation.")
    run_parser.add_argument("--no-install", action="store_true", help="Skip dependency bootstrap.")
    run_parser.add_argument("--no-execute", action="store_true", help="Inspect only; don't run scripts.")
    run_parser.add_argument("--skip-heavy", action="store_true",
                            help="Skip GPU and heavy-compute scripts; replicate from intermediate results only.")
    run_parser.add_argument("--timeout-seconds", type=int, default=600, help="Per-script timeout.")
    run_parser.add_argument("--stata-bin", default=None, help="Stata binary path for .do execution.")
    run_parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                            help="Logging verbosity.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        set_level(args.log_level)
        result = run_pipeline(
            paper_source=args.paper,
            package_source=args.package,
            output_dir=args.output_dir,
            execute=not args.no_execute,
            sandbox=not args.no_sandbox,
            install_dependencies=not args.no_install,
            timeout_seconds=args.timeout_seconds,
            stata_bin=args.stata_bin,
            skip_heavy=args.skip_heavy,
        )
        summary = result.comparison.summary
        verdict = result.analysis.adjusted_verdict if result.analysis else summary.verdict
        print(f"Verdict: {verdict}")
        if result.analysis and result.analysis.adjusted_verdict != summary.verdict:
            print(f"  (raw: {summary.verdict}, adjusted after filtering {result.analysis.coincidental_matches + result.analysis.coincidental_missing} coincidental claims)")
        print(
            f"Sandbox: {'enabled' if result.sandbox_manifest.enabled else 'disabled'} "
            f"with {len(result.sandbox_manifest.install_records)} bootstrap step(s)"
        )
        if result.analysis:
            print(
                "Match rates: "
                f"numbers={result.analysis.adjusted_numeric_rate:.1%} (substantive), "
                f"tables={summary.table_match_rate:.1%}, "
                f"figures={summary.figure_match_rate:.1%}"
            )
        else:
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
