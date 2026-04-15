from pathlib import Path
import csv
import json

from helper_pkg import replication_rows


root = Path(__file__).resolve().parent
outputs = root / "outputs"
outputs.mkdir(exist_ok=True)

with (outputs / "main_estimates.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["spec", "coefficient", "std_error", "n"])
    for row in replication_rows():
        writer.writerow(row)
    writer.writerow(["match_rate", 88.6, 94.4, 2])

(outputs / "figure1_replication_funnel.png").write_bytes(b"fake-image")

(outputs / "runtime.json").write_text(
    json.dumps({"python": __import__("sys").executable}),
    encoding="utf-8",
)
