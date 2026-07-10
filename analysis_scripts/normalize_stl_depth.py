#!/usr/bin/env python3
"""Normalize an STL surface depth to a target z-range.

The Savonius case is pseudo-2D: the background mesh is one cell thick in z and
uses empty front/back patches. For that to be valid, the blade STL must span
the full model depth instead of occupying only part of the thickness.
"""
import argparse
from pathlib import Path

import vtk


def normalize_depth(input_path: Path, output_path: Path, z_min: float, z_max: float) -> None:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(input_path))
    reader.Update()

    poly = vtk.vtkPolyData()
    poly.DeepCopy(reader.GetOutput())
    bounds = poly.GetBounds()
    old_min, old_max = bounds[4], bounds[5]
    old_span = old_max - old_min
    new_span = z_max - z_min
    if old_span <= 0:
        raise ValueError(f"Input STL has invalid z-span: {old_span}")
    if new_span <= 0:
        raise ValueError(f"Target z-span must be positive: {new_span}")

    points = poly.GetPoints()
    scale = new_span / old_span
    for i in range(points.GetNumberOfPoints()):
        x, y, z = points.GetPoint(i)
        z_new = z_min + (z - old_min) * scale
        points.SetPoint(i, x, y, z_new)
    points.Modified()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = vtk.vtkSTLWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputData(poly)
    writer.SetFileTypeToASCII()
    writer.Write()

    print(f"wrote {output_path}")
    print(f"z-range: {old_min:.9g}..{old_max:.9g} -> {z_min:.9g}..{z_max:.9g}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize STL z-depth")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--z-min", type=float, default=-0.1)
    parser.add_argument("--z-max", type=float, default=0.1)
    args = parser.parse_args()
    normalize_depth(args.input, args.output, args.z_min, args.z_max)


if __name__ == "__main__":
    main()
