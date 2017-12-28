from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.AbstractPlot import AbstractPlot




class TempoPlot(AbstractPlot):

    """Temporal XY-t plot."""

    def __init__(self,topWindow):
        super().__init__(topWindow)

    def draw(self,data:object,plotOptions:dict)->None:
        """
        
        :param data: 
        :param plotOptions: dict with useful info about plot.
        :return:
        """
        pyplot.plot(data['Recording timestamp'], data['Gaze point X'], 'r')
        pyplot.plot(data['Recording timestamp'], data['Gaze point Y'], 'b')
        pyplot.title('Временная развертка\ninterval: '+plotOptions['intId'])
        pyplot.xlabel('Recording timestamp (s)\n'+plotOptions['id'])
        pyplot.ylabel('Gaze point (px)\n'+plotOptions['id'])
        pyplot.axis(ymin=0,ymax=self.videoEyWidthPx)
        pyplot.grid(True)

    def drawByIntervals(self,data:object)->None:
        """
        
        :param data: 
        :return: 
        """
        pyplot.figure(figsize=(12,6))
        super().drawByIntervals(data)