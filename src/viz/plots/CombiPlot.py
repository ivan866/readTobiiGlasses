from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.GazePlot import GazePlot



class CombiPlot(GazePlot):
    """Both temporal and spatial plots stacked on top of each other, plus pupil diameter, eye velocity and acceleration."""

    def __init__(self,topWindow):
        GazePlot.__init__(self,topWindow)

    def draw(self,multiData:object)->None:
        chData = multiData.getChannelById('gaze', 'N')
        data = multiData.getDataBetween(chData, '5:00', '6:30.750')

        pyplot.figure(1,figsize=(6, 8))
        pyplot.subplot(211)
        pyplot.plot(data['Recording timestamp'], data['Gaze point X'], 'r')
        pyplot.plot(data['Recording timestamp'], data['Gaze point Y'], 'b')
        pyplot.title('5:00 - 6:30.750')
        pyplot.xlabel('Recording timestamp (s)')
        pyplot.ylabel('Gaze point (px)')
        pyplot.axis(ymin=0, ymax=self.videoEyWidthPx)
        pyplot.grid(True)

        pyplot.subplot(212)
        pyplot.plot(data['Gaze point X'], data['Gaze point Y'])
        pyplot.xlabel('Gaze point X (px)')
        pyplot.ylabel('Gaze point Y (px)')
        pyplot.axis([0, self.videoEyWidthPx, 0, self.videoEyHeightPx])
        pyplot.grid(True)

        pyplot.show()