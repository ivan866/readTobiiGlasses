

class GazePlot():

    """Base class for gaze plots."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.videoEyWidthPx=1920
        self.videoEyHeightPx=1080



class StubPlot(GazePlot):
    def __init__(self,topWindow):
        GazePlot.__init__(self,topWindow)

    def draw(self):
        self.topWindow.setStatus('Not implemented.')