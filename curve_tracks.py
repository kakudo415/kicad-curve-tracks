import pcbnew
import wx
import os

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

def get_tangent(tracks, t0):
    tangents  = []
    for t1 in tracks:
        if (t0.GetStart() != t1.GetStart() or t0.GetEnd() != t1.GetEnd()) and is_connected(t0, t1):
            tangents.append(t1)
    return tangents

class CurveTracks(pcbnew.ActionPlugin):
    def defaults(self):
        self.name                = "Curve Tracks"
        self.category            = "Wiring"
        self.description         = "Filling the gaps between tracks with curve"
        self.show_toolbar_button = True
        self.icon_file_name      = os.path.join(os.path.dirname(__file__), "icon.png")
    
    def Run(self):
        pcb      = pcbnew.GetBoard()
        tracks   = pcb.GetTracks()

        selected_track = get_selected_track(tracks)
        if selected_track is None:
            show_message("ERROR: TRACK UNSELECTED.")
            return

        tangents = get_tangent(tracks, selected_track)
        if len(tangents) != 2:
            show_message("ERROR: TANGENT COUNT MUST BE 2. BUT GIVEN {}.".format(len(tangents)))
            return

        selected_track.DeleteStructure()
