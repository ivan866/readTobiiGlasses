from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.AbstractPlot import AbstractPlot




class SpatialPlot(AbstractPlot):
    """Spatial X-Y plot, overlayed on stimulus image."""

    def __init__(self,topWindow):
        super().__init__(topWindow)


    def draw(self,data:object,plotOptions:dict)->None:
        """Actual plotting.
        
        :param data: 
        :param plotOptions: dict with useful info about plot.
        :return: 
        """
        #TODO sides proportion equal to camera
        pyplot.plot(data['Gaze point X'], data['Gaze point Y'])
        pyplot.title('Пространственная развертка\ninterval: '+plotOptions['intId'])
        pyplot.xlabel('Gaze point X (px)\n'+plotOptions['id'])
        pyplot.ylabel('Gaze point Y (px)\n'+plotOptions['id'])
        pyplot.axis([0,self.videoEyWidthPx,0,self.videoEyHeightPx])
        pyplot.grid(True)

    def drawByIntervals(self, data: object) -> None:
        """

        :param data: 
        :return: 
        """
        pyplot.figure(figsize=(6, 8))
        super().drawByIntervals(data)