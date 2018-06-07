from matplotlib import pyplot

from SettingsReader import SettingsReader





#TODO проверить возможность чертить графики через +gnuplot или !plplot




class AbstractViz():
    """Abstract visualization class with some useful data management methods."""

    def __init__(self, topWindow):
        self.topWindow = topWindow
        self.settingsReader = SettingsReader.getReader()


    def draw(self, data: object) -> None:
        """Method stub.

        :param data: DataFrame or Series, or list.
        :return: 
        """
        pass

    def drawByIntervals(self, data: object) -> None:
        """Automagically split data by intervals and draw all of them.

        :param data: 
        :return: 
        """
        #TODO all data channels
        self.topWindow.setStatus('Plotting...')
        ids=data.multiData['gaze']
        ints=self.settingsReader.getIntervals()
        plotNum=0
        for id in ids:
            chData=data.getChannelAndTag('gaze', id)

            for interval in ints:
                plotNum=plotNum+1
                intId=interval.get('id')
                vizData=chData[chData['Interval'] == intId]
                pyplot.subplot(len(ids),len(ints),plotNum)
                self.draw(vizData,plotOptions={'id':id,'intId':intId})
        pyplot.show()