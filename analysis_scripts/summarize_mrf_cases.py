#!/usr/bin/env python3
"""Summarize force coefficients across Savonius MRF cases."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


def read_angle(case: Path) -> float | None:
    info = case / "ANGLE_INFO.txt"
    if info.is_file():
        for line in info.read_text(encoding="ascii", errors="ignore").splitlines():
            if line.startswith("angle_deg="):
                try:
                    return float(line.split("=", 1)[1].strip())
                except ValueError:
                    return None

    if case.name == "savonius_mrf":
        return 0.0
    if "rot90cw" in case.name:
        return -90.0
    return None


def load_force_coeffs(path: Path) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        try:
            rows.append([float(item) for item in parts[:6]])
        except ValueError:
            continue
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize MRF force coefficient outputs")
    parser.add_argument("cases", nargs="+", type=Path, help="Case directories")
    parser.add_argument("-o", "--output-prefix", type=Path, default=Path("analysis_outputs/mrf_angle_summary"))
    parser.add_argument("--mean-window", type=int, default=10, help="Rows used for tail average")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for case in args.cases:
        coeff_path = case / "postProcessing/forceCoeffs1/0/forceCoeffs.dat"
        if not coeff_path.is_file():
            print(f"SKIP {case}: forceCoeffs.dat not found")
            continue

        data = load_force_coeffs(coeff_path)
        if not data:
            print(f"SKIP {case}: no usable rows in forceCoeffs.dat")
            continue

        tail = data[-min(args.mean_window, len(data)) :]
        last = data[-1]
        tail_cm = sum(row[1] for row in tail) / len(tail)
        tail_cd = sum(row[2] for row in tail) / len(tail)
        tail_cl = sum(row[3] for row in tail) / len(tail)

        summary_rows.append(
            {
                "case": case.name,
                "angle_deg": read_angle(case),
                "n_rows": len(data),
                "last_time": last[0],
                "last_cm": last[1],
                "last_cd": last[2],
                "last_cl": last[3],
                "mean_cm": tail_cm,
                "mean_cd": tail_cd,
                "mean_cl": tail_cl,
            }
        )

    if not summary_rows:
        raise SystemExit("No valid cases to summarize.")

    summary_rows.sort(key=lambda row: (math.inf if row["angle_deg"] is None else row["angle_deg"], row["case"]))

    csv_path = output_prefix.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    metrics = [
        ("mean_cm", "Cm"),
        ("mean_cd", "Cd"),
        ("mean_cl", "Cl"),
    ]

    x_labels = []
    x_values = []
    for idx, row in enumerate(summary_rows):
        if row["angle_deg"] is None:
            x_values.append(float(idx))
            x_labels.append(row["case"])
        else:
            x_values.append(float(row["angle_deg"]))
            x_labels.append(f"{row['angle_deg']:.0f}")

    for ax, (key, label) in zip(axes, metrics):
        y_values = [row[key] for row in summary_rows]
        ax.plot(x_values, y_values, marker="o", linewidth=1.8)
        for x, y, row in zip(x_values, y_values, summary_rows):
            ax.annotate(row["case"], (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("Angle [deg] if known, else case index")
    axes[-1].set_xticks(x_values)
    axes[-1].set_xticklabels(x_labels, rotation=20, ha="right")
    fig.suptitle("Savonius MRF Tail-Averaged Force Coefficients")
    fig.tight_layout()

    png_path = output_prefix.with_suffix(".png")
    fig.savefig(png_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    md_path = output_prefix.with_suffix(".md")
    with md_path.open("w", encoding="ascii") as handle:
        handle.write("# MRF Angle Summary\n\n")
        handle.write("| case | angle_deg | last_time | mean_cm | mean_cd | mean_cl |\n")
        handle.write("|---|---:|---:|---:|---:|---:|\n")
        for row in summary_rows:
            angle_text = "" if row["angle_deg"] is None else f"{row['angle_deg']:.1f}"
            handle.write(
                f"| {row['case']} | {angle_text} | {row['last_time']:.6g} | "
                f"{row['mean_cm']:.6g} | {row['mean_cd']:.6g} | {row['mean_cl']:.6g} |\n"
            )

    print(f"Wrote {csv_path}")
    print(f"Wrote {png_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
