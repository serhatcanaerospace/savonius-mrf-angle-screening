import sys
import vtk

def rotate_stl(infile, outfile, angle_deg, center=(1, 1, 0)):
    """Rotate an STL about +z axis through `center`.
    Positive angle_deg = counter-clockwise (right-hand rule, matches OpenFOAM
    MRF `omega` sign convention used in this project).
    Negative angle_deg = clockwise.
    """
    reader = vtk.vtkSTLReader()
    reader.SetFileName(infile)
    reader.Update()

    t = vtk.vtkTransform()
    t.Translate(center[0], center[1], center[2])
    t.RotateZ(angle_deg)
    t.Translate(-center[0], -center[1], -center[2])

    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetTransform(t)
    tf.SetInputConnection(reader.GetOutputPort())
    tf.Update()

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(outfile)
    writer.SetInputConnection(tf.GetOutputPort())
    writer.SetFileTypeToASCII()
    writer.Write()
    print(f"Wrote {outfile}: rotated {angle_deg} deg about z through {center}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: rotate_blade.py <in.stl> <out.stl> <angle_deg (+CCW/-CW)>")
        sys.exit(1)
    rotate_stl(sys.argv[1], sys.argv[2], float(sys.argv[3]))
