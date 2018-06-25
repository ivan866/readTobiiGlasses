from pandas import DataFrame

from matplotlib import pyplot

from viz.plots.AbstractPlot import AbstractPlot



class CombiPlot(AbstractPlot):
    """Both temporal and spatial plots stacked on top of each other, plus pupil diameter, eye velocity and acceleration."""

    def __init__(self,topWindow):
        super().__init__(topWindow)


    def draw(self,data:object,plotOptions:dict)->None:
        """

        :param data:
        :param plotOptions:
        :return:
        """
        pyplot.subplot(211)
        pyplot.plot(data['Recording timestamp'], data['Gaze point X'], 'r')
        pyplot.plot(data['Recording timestamp'], data['Gaze point Y'], 'b')
        pyplot.title('Комбинированный график\ninterval: '+plotOptions['intId'])
        pyplot.xlabel('Recording timestamp (s)\n'+plotOptions['id'])
        pyplot.ylabel('Gaze point (px)\n'+plotOptions['id'])
        pyplot.axis(ymin=0, ymax=self.videoEyWidthPx)
        pyplot.grid(True)

        pyplot.subplot(212)
        pyplot.plot(data['Gaze point X'], data['Gaze point Y'])
        pyplot.xlabel('Gaze point X (px)\n'+plotOptions['id'])
        pyplot.ylabel('Gaze point Y (px)\n'+plotOptions['id'])
        pyplot.axis([0, self.videoEyWidthPx, 0, self.videoEyHeightPx])
        pyplot.grid(True)


    def drawByIntervals(self, data: object) -> None:
        """

        :param data:
        :return:
        """
        pyplot.figure(figsize=(6, 8))
        super().drawByIntervals(data)