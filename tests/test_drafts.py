import numpy as np
import pandas as pd

from indexkit.data import config, output_root
from indexkit.drafts import generate
from indexkit.options import artifacts, digital


def test_generated_numbers_and_author_placeholders():
    reports = output_root() / "reports"
    reports.mkdir(parents=True)
    # Explicit input fixture tables; no market-performance claim.
    for name in ("summary.csv", "bootstrap.csv", "drawdown.csv"):
        pd.DataFrame({"fixture_value": [0.12345]}).to_csv(reports / name, index=False)
    c = config()
    artifacts(c)
    numbers = generate(c)
    for note in ("note1_index_results.md", "note2_digital_greeks.md"):
        text = (output_root() / "docs/drafts" / note).read_text()
        assert "[AUTHOR WRITES]" in text
    assert "0.12345" in (output_root() / "docs/drafts/note1_index_results.md").read_text()
    for row in numbers.itertuples():
        h = row.spot * 1e-5
        delta_up = digital(row.spot + h, row.strike, row.expiry, row.rate, row.vol, row.q)["delta"]
        delta_down = digital(row.spot - h, row.strike, row.expiry, row.rate, row.vol, row.q)[
            "delta"
        ]
        np.testing.assert_allclose(
            row.gamma, (delta_up - delta_down) / (2 * h), rtol=1e-4, atol=1e-10
        )
