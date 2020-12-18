import pcbnew
import wx
import os
import math

def c(constant, p):
    return pcbnew.wxPoint(constant * p.x, constant * p.y)

def d(v):
    return math.sqrt(v[0]**2 + v[1]**2)

class QuadBezierCurve:
    p0 = pcbnew.wxPoint(0, 0)
    p1 = pcbnew.wxPoint(0, 0)
    p2 = pcbnew.wxPoint(0, 0)

    def __init__(self, p0, p1, p2):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2

    def coord(self, t):
        return c(t*t, self.p0) + c(2*t*(1-t), self.p1) + c((1-t)*(1-t), self.p2)

class CubicBezierCurve:
    p0 = pcbnew.wxPoint(0, 0)
    p1 = pcbnew.wxPoint(0, 0)
    p2 = pcbnew.wxPoint(0, 0)
    p3 = pcbnew.wxPoint(0, 0)

    def __init__(self, p0, p1, p2, p3):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
    
    def coord(self, t):
        return c(t**3, self.p0) + c(3*t**2*(1-t), self.p1) + c(3*t*(1-t)**2, self.p2) + c((1-t)**3, self.p3)

class Dialog(wx.Dialog):
    def __init__(self, parent, msg):
        wx.Dialog.__init__(self, parent, id = -1, title = "Curve Tracks")
        panel = wx.Panel(self)
        message = wx.StaticText(panel, label = msg)

    def OnClose(self, e):
        e.Skip()
        self.Close()

def show_message(msg):
    dialog = Dialog(None, msg)
    dialog.ShowModal()
    dialog.Destroy()

def track_to_string(t):
    return "({0}, {1})".format(point_to_string(t.GetStart()), point_to_string(t.GetEnd()))

def point_to_string(p):
    return "({0}mm, {1}mm)".format(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))

def get_selected_track(tracks):
    for t in tracks:
        if t.IsSelected():
            return t
    return None

def is_connected(t0, t1):
    return t0.GetStart() == t1.GetStart() or t0.GetStart() == t1.GetEnd() or t0.GetEnd() == t1.GetStart() or t0.GetEnd() == t1.GetEnd()

def get_orthogonal(v):
    return [v[1], -v[0]]

def get_orthogonal_line(v0, v1, c):
    vo = (v0-c) if d(v0-c) > d(v1-c) else (v1-c)
    return [c, c + pcbnew.wxPoint(*get_orthogonal(vo))]

def is_parallel(v0, v1):
    v1o = get_orthogonal(v1)
    return v0[0] * v1o[0] + v0[1] * v1o[1] == 0

def get_tangent(tracks, t0):
    tangents  = []
    for t1 in tracks:
        if (t0.GetStart() != t1.GetStart() or t0.GetEnd() != t1.GetEnd()) and is_connected(t0, t1):
            tangents.append(t1)
    return tangents

def get_intersection(v0s, v0e, v1s, v1e):
    a0x = v0s.x
    a0y = v0s.y
    a1x = v0e.x
    a1y = v0e.y
    b0x = v1s.x
    b0y = v1s.y
    b1x = v1e.x
    b1y = v1e.y

    if is_parallel([a0x - a1x, a0y - a1y], [b0x - b1x, b0y - b1y]):
        return None

    if (a0x - a1x) == 0:
        x = a0x
        y = float(b0y - b1y) / (b0x - b1x) * (x - b0x) + b0y
        return pcbnew.wxPoint(x, y)

    if (b0x - b1x) == 0:
        x = b0x
        y = float(a0y - a1y) / (a0x - a1x) * (x - a0x) + a0y
        return pcbnew.wxPoint(x, y)

    s0 = float(a0y - a1y) / (a0x - a1x)
    s1 = float(b0y - b1y) / (b0x - b1x)

    x = (s1*b0x - s0*a0x + a0y - b0y) / (s1 - s0)
    y = s0 * (x - a0x) + a0y

    return pcbnew.wxPoint(x, y)

def get_length(v):
    return math.sqrt(v.x*v.x + v.y*v.y)

def get_closer_point(p0, p1, p2):
    return p1 if get_length(p0 - p1) < get_length(p0 - p2) else p2

def get_lines_coord(bezier):
    coords = []
    n = 32
    for _t in range(n):
        t = float(_t) / (n-1)
        coords.append(bezier.coord(t))
    lines = []
    for i in range(len(coords)):
        if i == 0:
            continue
        lines.append((coords[i-1], coords[i]))
    return lines

class CurveTracks(pcbnew.ActionPlugin):
    def defaults(self):
        self.name                = "Curve Tracks"
        self.category            = "Wiring"
        self.description         = "Filling the gaps between tracks with curve"
        self.show_toolbar_button = True
        self.icon_file_name      = os.path.join(os.path.dirname(__file__), "icon.png")

    def new_track(self, coord, w, layer):
        t = pcbnew.TRACK(self.pcb)
        t.SetStart(coord[0])
        t.SetEnd(coord[1])
        t.SetWidth(w)
        t.SetLayer(layer)
        return t

    def draw_track(self, bezier, template):
        for c in get_lines_coord(bezier):
            t = self.new_track(c, template.GetWidth(), template.GetLayer())
            self.pcb.Add(t)

    def Run(self):
        self.pcb = pcbnew.GetBoard()
        tracks   = self.pcb.GetTracks()

        selected_track = get_selected_track(tracks)
        if selected_track is None:
            show_message("ERROR: TRACK UNSELECTED.")
            return

        tangents = get_tangent(tracks, selected_track)
        if len(tangents) != 2:
            show_message("ERROR: TANGENT COUNT MUST BE 2. BUT GIVEN {}.".format(len(tangents)))
            return

        bezier = None

        intersection = get_intersection(tangents[0].GetStart(), tangents[0].GetEnd(), tangents[1].GetStart(), tangents[1].GetEnd())

        if intersection is None:
            points = [
                get_closer_point(selected_track.GetStart(), tangents[0].GetStart(), tangents[0].GetEnd()),
                get_closer_point(selected_track.GetStart(), tangents[1].GetStart(), tangents[1].GetEnd()),
            ]
            perpendicular_intersection = get_intersection(tangents[0].GetStart(), tangents[0].GetEnd(), *get_orthogonal_line(tangents[1].GetStart(), tangents[1].GetEnd(), points[1]))
            points.insert(1, c(0.5, points[0] + perpendicular_intersection))
            perpendicular_intersection = get_intersection(tangents[1].GetStart(), tangents[1].GetEnd(), *get_orthogonal_line(tangents[0].GetStart(), tangents[0].GetEnd(), points[0]))
            points.insert(2, c(0.5, points[2] + perpendicular_intersection))
            bezier = CubicBezierCurve(*points)
        else:
            points = [
                get_closer_point(intersection, tangents[0].GetStart(), tangents[0].GetEnd()),
                intersection,
                get_closer_point(intersection, tangents[1].GetStart(), tangents[1].GetEnd()),
            ]
            bezier = QuadBezierCurve(*points)

        self.draw_track(bezier, selected_track)

        # selected_track.DeleteStructure() TODO: This method will cause crash when use Ctrl + Z
        # self.pcb.Delete(selected_track) TODO: This method will also cause crash when use Ctrl + Z
