import pcbnew
import os

class ArcTracks(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Arc Tracks"
        self.description = "Filling the gaps between tracks with arc"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")
    
    def Run(self):
        print("hoge")
