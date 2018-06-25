import matplotlib
import matplotlib.pylab as pylab
matplotlib.rcParams['backend'] = "TkAgg"
matplotlib.style.use('bmh') #bmh, ggplot, seaborn
params = {
          #'font.family': 'arial',
          'figure.figsize': (8, 6),
          #'figure.dpi': 150,
          'axes.titlesize': 'small',
          'axes.labelsize': 'small',
          #'axes.facecolor': '#E8DDCB',
          'axes.grid': True,
          'axes.grid.which': 'major',    #both, major
          'axes.axisbelow': True,    #line, False
          #'grid.linewidth': 0.8,    #line, False
          #'grid.alpha': 0.8,    #line, False
          'xtick.labelsize': 'x-small',
          'ytick.labelsize': 'x-small',
          'xtick.direction': 'out',
          'ytick.direction': 'out',
          #'xtick.top': True,
          'ytick.left': True,
          'xtick.bottom': True,
          #'ytick.right': True,
          #'xtick.minor.top': True,
          'ytick.minor.left': True,
          'xtick.minor.bottom': True,
          #'ytick.minor.right': True,
          'xtick.minor.visible': True,
          'ytick.minor.visible': True,
          'legend.fontsize': 'xx-small',
          'legend.facecolor': 'darkgrey',
          'hist.bins': 50,
          'boxplot.notch': True,
          'boxplot.showmeans': True,
          'boxplot.showcaps': True,
          'boxplot.meanline': True,
          'errorbar.capsize': 10
          }
pylab.rcParams.update(params)


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