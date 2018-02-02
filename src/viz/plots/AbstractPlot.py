from viz.AbstractViz import AbstractViz




#TODO heatmap uses gaze 3d position and direction to project samples on sphere from inside; heatmap is spherical+able to render a plane projection, like an atlas

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