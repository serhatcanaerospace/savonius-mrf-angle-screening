#!/usr/bin/env pvbatch
"""Render a Savonius blade pressure screenshot with ParaView."""
import argparse
from pathlib import Path

from paraview.simple import (
    ColorBy,
    GetColorTransferFunction,
    LegacyVTKReader,
    Render,
    SaveScreenshot,
    Show,
    CreateView,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="ParaView pressure screenshot for Savonius_*.vtk")
    parser.add_argument("vtk", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("paraview_blade_pressure.png"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    reader = LegacyVTKReader(FileNames=[str(args.vtk.resolve())])
    view = CreateView("RenderView")
    view.ViewSize = [1400, 1000]
    view.Background = [1, 1, 1]
    display = Show(reader, view)
    ColorBy(display, ("CELLS", "p"))
    lut = GetColorTransferFunction("p")
    lut.ApplyPreset("Cool to Warm", True)
    display.RescaleTransferFunctionToDataRange(True, False)
    display.SetScalarBarVisibility(view, True)
    view.CameraPosition = [1, 1, 3]
    view.CameraFocalPoint = [1, 1, 0]
    view.CameraViewUp = [0, 1, 0]
    view.ResetCamera()
    Render(view)
    SaveScreenshot(str(args.output.resolve()), view)
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
