"""Generate numbers-only author draft boxes; never supply thesis or interpretation."""

import shutil

import numpy as np
import pandas as pd

from .data import output_root
from .options import digital


def table(frame):
    headers = list(frame.columns)
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(rows)


def generate(cfg):
    reports, docs = output_root() / "reports", output_root() / "docs/drafts"
    docs.mkdir(parents=True, exist_ok=True)
    sections = ["# Index results — author draft", "## Numbers box (computed sources)"]
    for source in ("summary.csv", "bootstrap.csv", "drawdown.csv"):
        sections.extend([f"### Source: reports/{source}", table(pd.read_csv(reports / source))])
    for heading in ("Thesis", "Interpretation", "Risks", "What would change the view"):
        sections.extend([f"## {heading}", "[AUTHOR WRITES]"])
    (docs / "note1_index_results.md").write_text("\n\n".join(sections) + "\n")
    p = cfg["options"]
    values = []
    for expiry in cfg["drafts"]["expiry_times"]:
        for ratio in cfg["drafts"]["spot_ratios"]:
            g = digital(p["spot"] * ratio, p["strike"], expiry, p["rate"], p["vol"], p["q"])
            values.append(
                dict(
                    spot=p["spot"] * ratio,
                    strike=p["strike"],
                    expiry=expiry,
                    rate=p["rate"],
                    q=p["q"],
                    vol=p["vol"],
                    delta=float(g["delta"]),
                    gamma=float(g["gamma"]),
                )
            )
    numbers = pd.DataFrame(values)
    numbers.to_csv(reports / "digital_greeks.csv", index=False)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    times = np.geomspace(
        min(cfg["drafts"]["expiry_times"]), max(cfg["drafts"]["expiry_times"]), 200
    )
    g = digital(p["spot"], p["strike"], times, p["rate"], p["vol"], p["q"])
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, field in zip(axes, ["delta", "gamma"]):
        ax.plot(times, g[field])
        ax.set(xlabel="Years to expiry", ylabel=field, title="Illustrative cash digital at spot")
    fig.tight_layout()
    fig.savefig(reports / "digital_greeks.png")
    plt.close(fig)
    for name in ("digital_greeks.png", "digital_delta.png"):
        shutil.copy2(reports / name, docs / name)
    content = [
        "# Digital Greeks — author draft",
        "## Numbers box",
        "Source: reports/digital_greeks.csv; analytic cash-or-nothing call, unit cash.",
        table(pd.read_csv(reports / "digital_greeks.csv")),
        "![Computed digital delta/gamma](digital_greeks.png)",
        "![Computed digital delta near expiry](digital_delta.png)",
    ]
    for heading in (
        "Thesis",
        "Explanation of near-expiry behavior",
        "Interpretation",
        "Risks and assumptions",
        "What would change the view",
    ):
        content.extend([f"## {heading}", "[AUTHOR WRITES]"])
    (docs / "note2_digital_greeks.md").write_text("\n\n".join(content) + "\n")
    return numbers
