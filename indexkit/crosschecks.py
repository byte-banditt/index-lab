"""Actual equity MC/IV, Java and optional R checks for full builds."""

import importlib.util
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from .data import ROOT, output_root
from .index_engine import metrics
from .options import digital, implied_vol, monte_carlo, vanilla


def equity_checks(cfg):
    p = cfg["options"]
    args = (p["spot"], p["strike"], p["expiry"], p["rate"], p["vol"], p["q"])
    rows = []
    for is_digital in (False, True):
        exact = float((digital if is_digital else vanilla)(*args)["price"])
        mc, se = monte_carlo(
            *args, paths=cfg["mc_paths"], seed=cfg["seed"], digital_payoff=is_digital
        )
        rows.append(
            dict(
                check="digital_mc" if is_digital else "call_mc",
                analytic=exact,
                computed=mc,
                se=se,
                passed=abs(mc - exact) <= 3 * se,
            )
        )
    price = float(vanilla(*args)["price"])
    iv = implied_vol(price, p["spot"], p["strike"], p["expiry"], p["rate"], p["q"])
    computed = float(vanilla(p["spot"], p["strike"], p["expiry"], p["rate"], iv, p["q"])["price"])
    rows.append(
        dict(
            check="iv_round_trip",
            analytic=price,
            computed=computed,
            se=0,
            passed=abs(price - computed) < 1e-8,
        )
    )
    table = pd.DataFrame(rows)
    table.to_csv(output_root() / "reports/equity_crosschecks.csv", index=False)
    if not table.passed.all():
        raise ValueError(table.to_string(index=False))
    return table


def languages(result, cfg):
    statuses = {}
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        if shutil.which("javac") and shutil.which("java"):
            script = ROOT / "java_bs/generate_reference.py"
            spec = importlib.util.spec_from_file_location("reference", script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.generate(directory / "reference.csv")
            subprocess.run(
                ["javac", "-d", str(directory), str(ROOT / "java_bs/BlackScholes.java")],
                check=True,
                capture_output=True,
                text=True,
            )
            java = subprocess.run(
                ["java", "-cp", str(directory), "BlackScholes", str(directory / "reference.csv")],
                check=True,
                capture_output=True,
                text=True,
            )
            statuses["java"] = java.stdout.strip()
        else:
            statuses["java"] = "NOT DONE: javac/java unavailable; Java cross-check NOT RUN"
        if shutil.which("Rscript"):
            result.levels.to_csv(directory / "levels.csv")
            pd.DataFrame([metrics(result.levels, result.levels.return_, cfg)]).to_csv(
                directory / "expected.csv", index=False
            )
            checked = subprocess.run(
                [
                    "Rscript",
                    str(ROOT / "r_check/verify.R"),
                    str(directory / "levels.csv"),
                    str(directory / "expected.csv"),
                    str(cfg["risk_free"]),
                    str(cfg["annual_sessions"]),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            statuses["R"] = checked.stdout.strip()
        else:
            statuses["R"] = "NOT DONE: Rscript unavailable; R cross-check NOT RUN"
    (output_root() / "reports/language_crosschecks.json").write_text(json.dumps(statuses, indent=2))
    for value in statuses.values():
        print(value)
    return statuses
