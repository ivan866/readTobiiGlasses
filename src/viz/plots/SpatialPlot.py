from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.GazePlot import GazePlot




class SpatialPlot(GazePlot):
    """Spatial X-Y plot, overlayed on stimulus image."""

    def __init__(self,topWindow):
        GazePlot.__init__(self,topWindow)

    def draw(self,multiData:object)->None:
        #TODO
        chData=multiData.getChannelById('gaze', 'N')
        data=multiData.getDataBetween(chData,'5:00', '6:30.750')

        pyplot.figure(figsize=(6, 8))
        pyplot.plot(data['Gaze point X'], data['Gaze point Y'])
        pyplot.title('Пространственная развертка')
        pyplot.xlabel('Gaze point X (px)')
        pyplot.ylabel('Gaze point Y (px)')
        pyplot.axis([0,self.videoEyWidthPx,0,self.videoEyHeightPx])
        pyplot.grid(True)
        pyplot.show()