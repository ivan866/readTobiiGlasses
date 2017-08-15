

class GazePlot():

    """Base class for gaze plots."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.videoEyWidthPx=1920
        self.videoEyHeightPx=1080




class TempoPlot(GazePlot):

    """Temporal XY-t plot."""

    pass


class SpatialPlot(GazePlot):
    """Spatial X-Y plot, overlayed on stimulus image."""

    pass


class CombiPlot(GazePlot):
    """Both temporal and spatial plots stacked on top of each other, plus pupil diameter, eye velocity and acceleration."""

    pass


class StubPlot(GazePlot):
    def __init__(self,topWindow):
        GazePlot.__init__(self,topWindow)

    def draw(self):
        self.topWindow.setStatus('Not implemented.')