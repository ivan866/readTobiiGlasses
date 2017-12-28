from viz.AbstractViz import AbstractViz



class AbstractPlot(AbstractViz):

    """Base class for gaze plots."""

    def __init__(self,topWindow):
        super().__init__(topWindow)

        self.videoEyWidthPx=1920
        self.videoEyHeightPx=1080


    def drawByIntervals(self,data:object)->None:
        """Simple delegate stub.
        
        :param data: 
        :return: 
        """
        super().drawByIntervals(data)