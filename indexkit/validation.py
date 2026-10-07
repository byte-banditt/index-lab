"""Independent antithetic Philox simulation and computed autocall validation studies."""

import numpy as np
import pandas as pd

from .data import output_root
from .options import vanilla
from .structured import autocallable, greeks


def quote(p, paths, seed, steps):
    return autocallable(
        p["spot"],
        p["spot"],
        p["vol"],
        p["rate"],
        p["q"],
        p["observations"],
        p["coupon"],
        p["autocall_barrier"],
        p["knock_in"],
        paths,
        seed,
        steps,
    )


def independent(p, paths=100000, seed=43, steps=504):
    """Different RNG, antithetic pairs, log paths and vectorized redemption assignment."""
    if paths < 4 or paths % 2:
        raise ValueError("Independent simulation requires an even number of paths >=4")
    observations = np.asarray(p["observations"])
    grid = np.unique(np.r_[np.linspace(0, observations[-1], steps + 1), observations])
    rng = np.random.Generator(np.random.Philox(seed))
    log_spot = np.zeros(paths)
    minimum = log_spot.copy()
    sampled = []
    for before, after in zip(grid[:-1], grid[1:]):
        dt = after - before
        half = rng.normal(size=paths // 2)
        log_spot += (p["rate"] - p["q"] - p["vol"] ** 2 / 2) * dt
        log_spot += p["vol"] * np.sqrt(dt) * np.r_[half, -half]
        minimum = np.minimum(minimum, log_spot)
        if after in observations:
            sampled.append(log_spot.copy())
    values = np.exp(sampled)
    hits = values[:-1] >= p["autocall_barrier"]
    any_call = hits.any(axis=0)
    first = np.where(any_call, hits.argmax(axis=0), len(observations) - 1)
    discount = np.exp(-p["rate"] * observations)
    coupons = np.array([discount[: i + 1].sum() * p["coupon"] for i in first])
    principal = np.where((np.exp(minimum) <= p["knock_in"]) & (values[-1] < 1), values[-1], 1.0)
    pv = coupons + np.where(any_call, 1.0, principal) * discount[first]
    paired = (pv[: paths // 2] + pv[paths // 2 :]) / 2
    probability, errors = [], []
    for i in range(len(observations)):
        indicators = (any_call & (first == i)).astype(float)
        pairs = (indicators[: paths // 2] + indicators[paths // 2 :]) / 2
        probability.append(indicators.mean())
        errors.append(pairs.std(ddof=1) / np.sqrt(paths // 2))
    return dict(
        price=pv.mean(),
        se=paired.std(ddof=1) / np.sqrt(len(paired)),
        early_call_prob=probability,
        early_call_se=errors,
    )


def degenerate_checks(p, paths, seed):
    times = np.array(p["observations"])
    dfs = np.exp(-p["rate"] * times)
    rows = []
    for case, ac, ki, exact in [
        ("first_call", 0, p["knock_in"], dfs[0] * (1 + p["coupon"])),
        ("principal_and_coupons", 1e9, 0, dfs[-1] + p["coupon"] * dfs.sum()),
        (
            "short_put",
            1e9,
            1e9,
            dfs[-1]
            + p["coupon"] * dfs.sum()
            - vanilla(p["spot"], p["spot"], times[-1], p["rate"], p["vol"], p["q"], "put")["price"]
            / p["spot"],
        ),
    ]:
        got = quote(dict(p, autocall_barrier=ac, knock_in=ki), paths, seed, p["steps"])
        residual = got["price"] - exact
        rows.append(
            dict(
                case=case,
                price=got["price"],
                analytic=exact,
                se=got["se"],
                residual=residual,
                passed=abs(residual) <= 3 * got["se"] + 1e-12,
            )
        )
    return pd.DataFrame(rows)


def studies(cfg):
    p, v = cfg["structured"], cfg["validation"]
    rows = []
    for paths in v["paths"]:
        result = quote(p, paths, cfg["seed"], p["steps"])
        rows.append(
            dict(
                study="paths",
                paths=paths,
                steps=p["steps"],
                seed=cfg["seed"],
                price=result["price"],
                se=result["se"],
            )
        )
    for steps in v["steps"]:
        result = quote(p, v["seed_paths"], cfg["seed"], steps)
        rows.append(
            dict(
                study="steps",
                paths=v["seed_paths"],
                steps=steps,
                seed=cfg["seed"],
                price=result["price"],
                se=result["se"],
            )
        )
    for seed in range(cfg["seed"], cfg["seed"] + v["seed_count"]):
        result = quote(p, v["seed_paths"], seed, p["steps"])
        rows.append(
            dict(
                study="seeds",
                paths=v["seed_paths"],
                steps=p["steps"],
                seed=seed,
                price=result["price"],
                se=result["se"],
            )
        )
    table = pd.DataFrame(rows)
    table.to_csv(output_root() / "reports/autocall_convergence.csv", index=False)
    seeds = table[table.study == "seeds"].price.agg(["mean", "std", "min", "max"])
    seeds.to_csv(output_root() / "reports/autocall_seed_summary.csv")
    bumps = pd.DataFrame(
        [
            dict(
                bump=b,
                **greeks(dict(p, spot_bump_ratio=b, vol_bump=b), v["seed_paths"], cfg["seed"]),
            )
            for b in v["bumps"]
        ]
    )
    bumps.to_csv(output_root() / "reports/autocall_bumps.csv", index=False)
    checks = degenerate_checks(p, cfg["mc_paths"], cfg["seed"])
    checks.to_csv(output_root() / "reports/autocall_degenerate.csv", index=False)
    a = quote(p, cfg["mc_paths"], cfg["seed"], p["steps"])
    b = independent(p, cfg["mc_paths"], cfg["seed"] + 1, 2 * p["steps"])
    combined = np.hypot(a["se"], b["se"])
    comparison = pd.DataFrame(
        [
            dict(
                quantity="price",
                primary=a["price"],
                independent=b["price"],
                combined_se=combined,
                passed=abs(a["price"] - b["price"]) <= 3 * combined,
            )
        ]
    )
    for i, (pa, pb) in enumerate(zip(a["early_call_prob"], b["early_call_prob"])):
        se = np.hypot(np.sqrt(pa * (1 - pa) / cfg["mc_paths"]), b["early_call_se"][i])
        comparison.loc[len(comparison)] = [
            f"early_call_{i}",
            pa,
            pb,
            se,
            abs(pa - pb) <= 3 * se + 1e-12,
        ]
    comparison.to_csv(output_root() / "reports/autocall_independent.csv", index=False)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, kind, x in zip(axes, ["paths", "steps"], ["paths", "steps"]):
        part = table[table.study == kind]
        ax.errorbar(part[x], part.price, yerr=3 * part.se, marker="o")
        ax.set(xlabel=x, ylabel="Price; +/-3 standard errors", title=kind)
        if kind == "paths":
            ax.set_xscale("log")
    fig.tight_layout()
    fig.savefig(output_root() / "reports/autocall_convergence.png")
    plt.close(fig)
    text = [
        "# Autocall validation",
        "Illustrative GBM; coupon is per observation while alive.",
        "Exact observation nodes are inserted; knock-in remains discretely monitored.",
        "## Degenerate checks",
        checks.to_string(index=False),
        "## Independent Philox antithetic implementation",
        comparison.to_string(index=False),
        "## Seed statistics",
        seeds.to_string(),
        "## CRN bump study",
        bumps.to_string(index=False),
        "Bump variation is reported, not suppressed or declared stable without evidence.",
        "## Convergence",
        table.to_string(index=False),
    ]
    # pandas markdown has an optional dependency: use plain computed CSV fenced below instead.
    (output_root() / "docs/validation_autocall.md").write_text("\n\n".join(text) + "\n")
    return checks, comparison
