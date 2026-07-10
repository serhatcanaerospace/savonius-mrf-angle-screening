#!/usr/bin/env python3
"""Generate a useful ParaView visualization suite for Savonius OpenFOAM cases."""

from __future__ import annotations

import argparse
from pathlib import Path

from paraview.simple import *  # noqa: F401,F403


def parse_args():
    parser = argparse.ArgumentParser(description="Generate ParaView CFD screenshots for a case")
    parser.add_argument("case", type=Path, help="OpenFOAM case directory")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for PNG files",
    )
    parser.add_argument("--time", type=float, default=None, help="Specific time value, default=latest")
    return parser.parse_args()


def ensure_foam_file(case_dir: Path) -> Path:
    foam = case_dir / f"{case_dir.name}.foam"
    if not foam.exists():
        foam.touch()
    return foam


def setup_view():
    view = CreateView("RenderView")
    view.ViewSize = [2200, 1400]
    view.OrientationAxesVisibility = 0
    view.CenterAxesVisibility = 0
    view.UseLight = 1
    view.Background = [1.0, 1.0, 1.0]
    view.CameraParallelProjection = 0
    return view


def set_latest_time(source, time_value=None):
    animation_scene = GetAnimationScene()
    animation_scene.UpdateAnimationUsingDataTimeSteps()
    if time_value is None:
        if animation_scene.TimeKeeper.TimestepValues:
            animation_scene.AnimationTime = animation_scene.TimeKeeper.TimestepValues[-1]
    else:
        animation_scene.AnimationTime = time_value
    UpdatePipeline()


def reader_for_regions(foam_file: Path, regions):
    reader = OpenFOAMReader(FileName=str(foam_file))
    reader.MeshRegions = regions
    reader.CellArrays = ["U", "p", "k", "omega", "nut"]
    return reader


def apply_common_display(display, representation="Surface"):
    display.Representation = representation
    display.SetScalarBarVisibility(GetActiveView(), False)


def color_by_scalar(display, association, array_name, component=None):
    if component is None:
        ColorBy(display, (association, array_name))
    else:
        ColorBy(display, (association, array_name, component))
    display.RescaleTransferFunctionToDataRange(True, False)
    lut = GetColorTransferFunction(array_name)
    pwf = GetOpacityTransferFunction(array_name)
    lut.ApplyPreset("Cool to Warm", True)
    return lut, pwf


def add_scalar_bar(lut, title):
    bar = GetScalarBar(lut, GetActiveView())
    bar.Title = title
    bar.ComponentTitle = ""
    bar.WindowLocation = "Upper Right Corner"
    bar.TitleFontSize = 14
    bar.LabelFontSize = 12
    return bar


def save_png(output_dir: Path, name: str):
    SaveScreenshot(str(output_dir / name), GetActiveView(), ImageResolution=[2200, 1400])


def reset_camera_2d(view):
    view.CameraPosition = [2.4, 0.0, 18.0]
    view.CameraFocalPoint = [2.4, 0.0, 0.0]
    view.CameraViewUp = [0.0, 1.0, 0.0]
    view.CameraParallelProjection = 1
    view.CameraParallelScale = 2.6


def reset_camera_blade(view):
    view.CameraPosition = [2.2, -1.4, 2.8]
    view.CameraFocalPoint = [1.0, 1.0, 0.0]
    view.CameraViewUp = [0.0, 0.0, 1.0]
    view.CameraParallelProjection = 0


def reset_camera_3d(view):
    view.CameraPosition = [4.8, -4.5, 2.7]
    view.CameraFocalPoint = [1.8, 0.0, 0.0]
    view.CameraViewUp = [0.0, 0.0, 1.0]
    view.CameraParallelProjection = 0


def main():
    args = parse_args()
    case_dir = args.case.resolve()
    output_dir = args.output_dir or (Path("analysis_outputs") / f"{case_dir.name}_paraview")
    output_dir.mkdir(parents=True, exist_ok=True)

    foam_file = ensure_foam_file(case_dir)
    view = setup_view()
    SetActiveView(view)

    internal = reader_for_regions(foam_file, ["internalMesh"])
    blade = reader_for_regions(foam_file, ["patch/Savonius"])
    full = reader_for_regions(foam_file, ["internalMesh", "patch/Savonius"])

    set_latest_time(internal, args.time)
    set_latest_time(blade, args.time)
    set_latest_time(full, args.time)

    merged_internal = MergeBlocks(Input=internal)
    merged_blade = MergeBlocks(Input=blade)
    merged_full = MergeBlocks(Input=full)
    point_internal = CellDatatoPointData(Input=merged_internal)
    point_blade = CellDatatoPointData(Input=merged_blade)
    point_full = CellDatatoPointData(Input=merged_full)

    UpdatePipeline()

    roi_clip = Clip(Input=point_internal)
    roi_clip.ClipType = "Box"
    roi_clip.ClipType.Position = [-2.0, -3.0, -0.11]
    roi_clip.ClipType.Length = [8.0, 6.0, 0.22]

    z_slice = Slice(Input=roi_clip)
    z_slice.SliceType = "Plane"
    z_slice.SliceType.Origin = [2.0, 0.0, 0.0]
    z_slice.SliceType.Normal = [0.0, 0.0, 1.0]

    projected_velocity = Calculator(Input=z_slice)
    projected_velocity.ResultArrayName = "U_plane"
    projected_velocity.Function = "U_X*iHat + U_Y*jHat"

    seeds = Line()
    seeds.Point1 = [-1.5, -2.0, 0.0]
    seeds.Point2 = [-1.5, 2.0, 0.0]
    seeds.Resolution = 24

    stream = StreamTracer(Input=projected_velocity, SeedType="Line")
    stream.Vectors = ["POINTS", "U_plane"]
    stream.MaximumStreamlineLength = 30.0
    stream.MaximumSteps = 2500
    stream.InitialStepLength = 0.04
    stream.MinimumStepLength = 0.005
    stream.MaximumStepLength = 0.15
    stream.SeedType.Point1 = seeds.Point1
    stream.SeedType.Point2 = seeds.Point2
    stream.SeedType.Resolution = seeds.Resolution

    wake_metrics = Calculator(Input=point_internal)
    wake_metrics.ResultArrayName = "uDeficit"
    wake_metrics.Function = "6.0 - U_X"

    wake_clip = Clip(Input=wake_metrics)
    wake_clip.ClipType = "Box"
    wake_clip.ClipType.Position = [-1.5, -2.6, -0.11]
    wake_clip.ClipType.Length = [7.5, 5.2, 0.22]

    wake_slice = Slice(Input=wake_clip)
    wake_slice.SliceType = "Plane"
    wake_slice.SliceType.Origin = [3.5, 0.0, 0.0]
    wake_slice.SliceType.Normal = [0.0, 0.0, 1.0]

    stream3d = StreamTracer(Input=point_internal, SeedType="Line")
    stream3d.Vectors = ["POINTS", "U"]
    stream3d.MaximumStreamlineLength = 14.0
    stream3d.MaximumSteps = 2000
    stream3d.InitialStepLength = 0.04
    stream3d.MinimumStepLength = 0.005
    stream3d.MaximumStepLength = 0.15
    stream3d.SeedType.Point1 = [-1.0, -1.8, 0.0]
    stream3d.SeedType.Point2 = [-1.0, 1.8, 0.0]
    stream3d.SeedType.Resolution = 28

    stream3d_tube = Tube(Input=stream3d)
    stream3d_tube.Scalars = ["POINTS", "U"]
    stream3d_tube.Vectors = ["POINTS", "Normals"]
    stream3d_tube.Radius = 0.025
    stream3d_tube.NumberofSides = 16

    mesh_clip = Clip(Input=merged_internal)
    mesh_clip.ClipType = "Box"
    mesh_clip.ClipType.Position = [0.25, 0.2, -0.11]
    mesh_clip.ClipType.Length = [1.5, 1.6, 0.22]
    mesh_slice = Slice(Input=mesh_clip)
    mesh_slice.SliceType = "Plane"
    mesh_slice.SliceType.Origin = [1.0, 1.0, 0.0]
    mesh_slice.SliceType.Normal = [0.0, 0.0, 1.0]

    blade_surface = ExtractSurface(Input=point_blade)
    blade_thick = Transform(Input=blade_surface)
    blade_thick.Transform.Scale = [1.0, 1.0, 14.0]

    blade_display = Show(blade_thick, view)
    apply_common_display(blade_display, "Surface With Edges")
    blade_display.LineWidth = 1.5
    blade_display.EdgeColor = [0.08, 0.08, 0.08]
    blade_lut, _ = color_by_scalar(blade_display, "POINTS", "p")
    blade_lut.RescaleTransferFunction(-90.0, 30.0)
    add_scalar_bar(blade_lut, "Pressure p")
    reset_camera_blade(view)
    Render()
    save_png(output_dir, "01_blade_pressure_closeup.png")

    Hide(blade_thick, view)
    HideScalarBarIfNotNeeded(blade_lut, view)

    slice_display = Show(projected_velocity, view)
    apply_common_display(slice_display)
    u_lut, _ = color_by_scalar(slice_display, "POINTS", "U", "Magnitude")
    u_lut.ApplyPreset("Viridis (matplotlib)", True)
    u_lut.RescaleTransferFunction(0.0, 12.0)
    add_scalar_bar(u_lut, "Velocity |U|")
    stream_display = Show(stream, view)
    stream_display.Representation = "Surface"
    ColorBy(stream_display, ("POINTS", "U", "Magnitude"))
    stream_display.RescaleTransferFunctionToDataRange(True, False)
    stream_display.LineWidth = 3.0
    blade_overlay = Show(blade_surface, view)
    blade_overlay.Representation = "Surface"
    ColorBy(blade_overlay, None)
    blade_overlay.DiffuseColor = [0.08, 0.08, 0.08]
    blade_overlay.LineWidth = 2.0
    reset_camera_2d(view)
    Render()
    save_png(output_dir, "02_midplane_velocity_streamlines.png")

    Hide(projected_velocity, view)
    Hide(stream, view)
    Hide(blade_surface, view)
    HideScalarBarIfNotNeeded(u_lut, view)

    wake_display2d = Show(wake_slice, view)
    apply_common_display(wake_display2d)
    omega_lut, _ = color_by_scalar(wake_display2d, "POINTS", "uDeficit")
    omega_lut.ApplyPreset("Inferno (matplotlib)", True)
    omega_lut.RescaleTransferFunction(0.0, 6.0)
    add_scalar_bar(omega_lut, "Velocity deficit (6-Ux)")
    blade_overlay = Show(blade_surface, view)
    blade_overlay.Representation = "Surface"
    ColorBy(blade_overlay, None)
    blade_overlay.DiffuseColor = [0.05, 0.8, 0.9]
    view.CameraParallelScale = 2.2
    view.CameraFocalPoint = [2.0, 0.0, 0.0]
    view.CameraPosition = [2.0, 0.0, 18.0]
    view.CameraViewUp = [0.0, 1.0, 0.0]
    Render()
    save_png(output_dir, "03_midplane_wake_deficit.png")

    Hide(wake_slice, view)
    Hide(blade_surface, view)
    HideScalarBarIfNotNeeded(omega_lut, view)

    blade3d_display = Show(blade_thick, view)
    blade3d_display.Representation = "Surface"
    blade3d_lut, _ = color_by_scalar(blade3d_display, "POINTS", "p")
    blade3d_lut.RescaleTransferFunction(-90.0, 30.0)
    add_scalar_bar(blade3d_lut, "Pressure p")
    wake_slice_3d = Show(wake_slice, view)
    wake_slice_3d.Representation = "Surface"
    wake_slice_3d.Opacity = 0.18
    ColorBy(wake_slice_3d, ("POINTS", "uDeficit"))
    wake_display = Show(stream3d_tube, view)
    wake_display.Representation = "Surface"
    vort3d_lut, _ = color_by_scalar(wake_display, "POINTS", "U", "Magnitude")
    vort3d_lut.ApplyPreset("Turbo", True)
    vort3d_lut.RescaleTransferFunction(0.0, 10.0)
    add_scalar_bar(vort3d_lut, "3D streamtube |U|")
    reset_camera_3d(view)
    Render()
    save_png(output_dir, "04_3d_wake_structure.png")

    Hide(blade_thick, view)
    Hide(wake_slice, view)
    Hide(stream3d_tube, view)
    HideScalarBarIfNotNeeded(vort3d_lut, view)
    HideScalarBarIfNotNeeded(blade3d_lut, view)

    mesh_display = Show(mesh_slice, view)
    mesh_display.Representation = "Surface With Edges"
    ColorBy(mesh_display, None)
    mesh_display.DiffuseColor = [0.88, 0.88, 0.88]
    mesh_display.EdgeColor = [0.15, 0.15, 0.15]
    blade_overlay = Show(blade_surface, view)
    blade_overlay.Representation = "Surface"
    ColorBy(blade_overlay, None)
    blade_overlay.DiffuseColor = [0.85, 0.2, 0.2]
    view.CameraPosition = [1.0, 1.0, 16.0]
    view.CameraFocalPoint = [1.0, 1.0, 0.0]
    view.CameraViewUp = [0.0, 1.0, 0.0]
    view.CameraParallelProjection = 1
    view.CameraParallelScale = 1.15
    Render()
    save_png(output_dir, "05_local_mesh_near_blade.png")

    print(f"Saved screenshots to {output_dir}")


if __name__ == "__main__":
    main()
