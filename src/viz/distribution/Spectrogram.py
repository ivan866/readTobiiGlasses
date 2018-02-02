from scipy import signal

from matplotlib import pyplot

from viz.AbstractViz import AbstractViz



class Spectrogram(AbstractViz):

    """Spectrogram with colorbar."""

    def __init__(self,topWindow):
        super().__init__(topWindow)


    def draw(self,data:object,plotOptions:dict)->None:
        """Actually draw one single plot.
        
        :param data: DataFrame or Series, or list.
        :param plotOptions: dict with useful info about plot.
        :return: 
        """
        #TODO fix discretion of plot
        f, t, sxx = signal.spectrogram(data)
        pyplot.pcolormesh(t, f, sxx)
        pyplot.title('Спектрограмма\ninterval: '+plotOptions['intId'])
        pyplot.xlabel('Time (s)\n'+plotOptions['id'])
        pyplot.ylabel('Duration (s)\n'+plotOptions['id'])
        pyplot.colorbar()
        pyplot.grid(True)
        #pyplot.tight_layout()


    def drawByIntervals(self, data: object) -> None:
        """

        :param data:
        :return:
        """
        pyplot.figure(figsize=(12, 6))
        super().drawByIntervals(data)
