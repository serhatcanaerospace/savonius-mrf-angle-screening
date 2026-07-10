#!/usr/bin/env python3
"""Plot OpenFOAM forceCoeffs.dat for a Savonius case."""
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_force_coeffs(path: Path) -> np.ndarray:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 4:
                rows.append([float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])])
    if not rows:
        raise ValueError(f"No data rows found in {path}")
    return np.asarray(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Cm/Cd/Cl from forceCoeffs.dat")
    parser.add_argument(
        "case",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "savonius_mrf",
    )
    parser.add_argument("-o", "--output", type=Path, default=Path("force_coeffs.png"))
    args = parser.parse_args()

    data_path = args.case / "postProcessing/forceCoeffs1/0/forceCoeffs.dat"
    data = read_force_coeffs(data_path)
    time, cm, cd, cl = data.T

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(time, cm, label="Cm", lw=2)
    ax.plot(time, cd, label="Cd", lw=2)
    ax.plot(time, cl, label="Cl", lw=2)
    ax.axhline(0, color="0.25", lw=0.8)
    ax.set_xlabel("Iteration / pseudo-time")
    ax.set_ylabel("Coefficient")
    ax.set_title("Savonius force coefficients")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150)

    last = data[-1]
    window = data[-min(10, len(data)) :, 1:]
    print(f"saved: {args.output}")
    print(f"last: t={last[0]:g} Cm={last[1]:.6g} Cd={last[2]:.6g} Cl={last[3]:.6g}")
    print(
        "last_window_mean: "
        f"Cm={window[:,0].mean():.6g} Cd={window[:,1].mean():.6g} Cl={window[:,2].mean():.6g}"
    )


if __name__ == "__main__":
    main()
