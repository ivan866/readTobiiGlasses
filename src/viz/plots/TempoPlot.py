from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.GazePlot import GazePlot




class TempoPlot(GazePlot):

    """Temporal XY-t plot."""

    def __init__(self,topWindow):
        GazePlot.__init__(self,topWindow)

    def draw(self,multiData:object)->None:
        #TODO data acquisition
        chData=multiData.getChannelById('gaze', 'N')
        data=multiData.getDataBetween(chData,'5:00', '6:30.750')

        pyplot.figure(figsize=(12,6))
        pyplot.plot(data['Recording timestamp'],data['Gaze point X'],'r')
        pyplot.plot(data['Recording timestamp'], data['Gaze point Y'], 'b')
        pyplot.title('Временная развертка')
        pyplot.xlabel('Recording timestamp (s)')
        pyplot.ylabel('Gaze point (px)')
        pyplot.axis(ymin=0,ymax=self.videoEyWidthPx)
        pyplot.grid(True)
        pyplot.show()