#!/usr/bin/env python3
"""Create a rotated Savonius MRF case from an existing template case."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import vtk


GENERATED_NAMES = {
    "VTK",
    "postProcessing",
    "processor0",
    "processor1",
    "processor2",
    "processor3",
    "processor4",
    "processor5",
    "processor6",
    "processor7",
    "constant/polyMesh",
}


def is_generated(rel_path: Path) -> bool:
    rel_text = rel_path.as_posix()
    if rel_text in GENERATED_NAMES:
        return True
    if rel_text.startswith("constant/polyMesh/"):
        return True
    if rel_text.startswith("processor"):
        return True
    if rel_text.startswith("postProcessing/"):
        return True
    if rel_text.startswith("VTK/"):
        return True
    if rel_path.name.startswith("log."):
        return True
    if rel_path.suffix in {".foam", ".out"}:
        return True
    if rel_path.parts and rel_path.parts[0].replace(".", "", 1).isdigit():
        return True
    return False


def copy_case(template: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"Target case already exists: {target}")

    for src in template.rglob("*"):
        rel = src.relative_to(template)
        if is_generated(rel):
            continue
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def rotate_stl(src: Path, dst: Path, angle_deg: float, center=(1.0, 1.0, 0.0)) -> None:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(src))
    reader.Update()

    transform = vtk.vtkTransform()
    transform.Translate(center[0], center[1], center[2])
    transform.RotateZ(angle_deg)
    transform.Translate(-center[0], -center[1], -center[2])

    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetTransform(transform)
    transform_filter.SetInputConnection(reader.GetOutputPort())
    transform_filter.Update()

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(str(dst))
    writer.SetInputConnection(transform_filter.GetOutputPort())
    writer.SetFileTypeToASCII()
    writer.Write()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a rotated Savonius MRF case")
    parser.add_argument("template_case", type=Path, help="Existing case to copy")
    parser.add_argument("target_case", type=Path, help="New case directory to create")
    parser.add_argument("angle_deg", type=float, help="+CCW / -CW rotation angle")
    parser.add_argument(
        "--source-stl",
        type=Path,
        default=Path("geometry/rotorBlade_horizontal.stl"),
        help="Reference STL to rotate",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template = args.template_case.resolve()
    target = args.target_case.resolve()
    source_stl = args.source_stl.resolve()

    if not template.is_dir():
        raise SystemExit(f"Template case not found: {template}")
    if not source_stl.is_file():
        raise SystemExit(f"Reference STL not found: {source_stl}")

    copy_case(template, target)

    target_stl = target / "constant/triSurface/rotorBlade.stl"
    target_stl.parent.mkdir(parents=True, exist_ok=True)
    rotate_stl(source_stl, target_stl, args.angle_deg)

    (target / "ANGLE_INFO.txt").write_text(
        "\n".join(
            [
                f"template_case={template}",
                f"source_stl={source_stl}",
                f"angle_deg={args.angle_deg}",
                "rotation_sign=+CCW,-CW",
            ]
        )
        + "\n",
        encoding="ascii",
    )

    print(f"Created {target}")
    print(f"Rotated STL written to {target_stl}")
    print(f"Angle metadata written to {target / 'ANGLE_INFO.txt'}")
    print("Next step: run ./Allrun-pre and then ./Allrun inside the new case.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
