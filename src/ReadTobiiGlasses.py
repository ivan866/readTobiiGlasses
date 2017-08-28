import argparse
from datetime import datetime
import sys
import webbrowser

import logging

from tkinter import *

import matplotlib
matplotlib.rcParams['backend'] = "TkAgg"

from SettingsReader import SettingsReader
from data.MultiData import MultiData
from data.DataReader import DataReader
from data.DataExporter import DataExporter
from stats.Stats import Stats
from viz.plots.GazePlot import StubPlot
from viz.plots.TempoPlot import TempoPlot
from viz.plots.SpatialPlot import SpatialPlot
from viz.plots.CombiPlot import CombiPlot




class ReadTobiiGlasses():

    """Main class of the utility.
    
    Maintains top level window with menus and a status bar.
    
    """

    def __init__(self,gui:bool=True):
        """Setup application and populate menu.
        
        :param gui: Whether to start gui.
        """
		#TODO CHANGES.TXT, study standard format
        #TODO add INSTALLING
        self.LOG_FORMAT="%(levelname)s %(asctime)s %(pathname)s at %(lineno)s - %(message)s"
        logging.basicConfig(filename='readTobiiGlasses.log',
                            level=logging.DEBUG,
                            format=self.LOG_FORMAT)
        self.logger=logging.getLogger()


        self.logger.debug('creating tk root..')
        self.root = Tk()
        self.root.geometry('640x400')
        self.root.title('Read Tobii Glasses')

        self.rootMenu = Menu(self.root)
        self.root.config(menu=self.rootMenu)


        self.logger.debug('creating report and status widgets...')
        self.status = Label(self.root, bd=1, relief=RIDGE, anchor=W)
        self.status.config(text='Please select settings.')
        self.status.pack(side=BOTTOM,fill=X)

        self.report=Text(self.root, bg='lightgray', relief=SUNKEN, wrap=WORD)
        self.report.insert('0.0',datetime.now().strftime('%Y-%m-%d') + '\n')
        self.appendReport('ReadTobiiGlasses started.')
        self.report.pack(side=LEFT,anchor=NW,fill=BOTH)


        #setup other classes
        self.logger.debug('instantiating classes...')
        self.settingsReader = SettingsReader(self)
        self.multiData = MultiData(self)
        self.dataReader = DataReader(self)
        self.dataExporter = DataExporter(self)

        self.stats = Stats(self)
        self.stubPlot = StubPlot(self)
        self.tempoPlot = TempoPlot(self)
        self.spatialPlot = SpatialPlot(self)
        self.combiPlot = CombiPlot(self)

        self.logger.debug('populating menus...')
        #populate menu
        settingsMenu = Menu(self.rootMenu, tearoff=0)
        settingsMenu.add_command(label="Select...", command=self.settingsReader.select)
        settingsMenu.add_command(label="Modify in external editor", command=self.settingsReader.open)
        self.rootMenu.add_cascade(label="Settings", menu=settingsMenu)

        dataMenu = Menu(self.rootMenu, tearoff=0)
        dataMenu.add_command(label="Parse settings and read data", command=lambda: self.dataReader.read(self.settingsReader,self.multiData))
        dataMenu.add_command(label="Summary and validation", command=self.multiData.validate)
        exportMenu = Menu(dataMenu, tearoff=0)
        exportMenu.add_command(label="Fixations to Excel", command=lambda: self.dataExporter.exportFixations(self.multiData,'xls'))
        exportMenu.add_command(label="Fixations to CSV", command=lambda: self.dataExporter.exportFixations(self.multiData,'csv'))
        exportMenu.add_command(label="Gyroscope data", command=lambda: self.dataExporter.exportGyro(self.multiData))
        exportMenu.add_command(label="Voc/ocul combined", command=lambda: self.setStatus('Not implemented.'))
        dataMenu.add_cascade(label="Export", menu=exportMenu)
        self.rootMenu.add_cascade(label="Data", menu=dataMenu)

        statsMenu = Menu(self.rootMenu, tearoff=0)
        statsMenu.add_command(label="Descriptive", command=lambda: self.stats.descriptive(self.multiData))
        # экспортируем и сразу открываем
        # statsMenu.add_command(label="Save report to Excel", command=self.stats.save)
        self.rootMenu.add_cascade(label="Statistics", menu=statsMenu)

        vizMenu = Menu(self.rootMenu, tearoff=0)
        plotMenu = Menu(vizMenu, tearoff=0)
        plotMenu.add_command(label="Temporal", command=lambda: self.tempoPlot.draw(self.multiData))
        plotMenu.add_command(label="Spatial", command=lambda: self.spatialPlot.draw(self.multiData))
        plotMenu.add_command(label="Combined", command=lambda: self.combiPlot.draw(self.multiData))
        vizMenu.add_cascade(label="Plots", menu=plotMenu)
        vizMenu.add_command(label="Gaze overlay animation", command=self.stubPlot.draw)
        vizMenu.add_command(label="3D gaze vectors", command=self.stubPlot.draw)
        vizMenu.add_command(label="Heatmap", command=self.stubPlot.draw)
        vizMenu.add_command(label="Intersection matrix", command=self.stubPlot.draw)
        self.rootMenu.add_cascade(label="Visualizations", menu=vizMenu)

        helpMenu = Menu(self.rootMenu, tearoff=0)
        helpMenu.add_command(label="Wiki", command=lambda: self.gotoWeb('wiki'))
        helpMenu.add_command(label="GitHub", command=lambda: self.gotoWeb('repo'))
        self.rootMenu.add_cascade(label="Help", menu=helpMenu)

        self.logger.debug('starting tk main loop...')
        if gui:
            self.root.mainloop()



    def appendReport(self,text:str) -> None:
        """Appends text to report text widget.
        
        :param text: Text to append.
        :return: 
        """
        #TODO add colorize text
        now = datetime.now().strftime('%H:%M:%S')
        self.report.config(state=NORMAL)
        self.report.insert(END,now+' '+text+'\n')
        self.report.see(END)
        self.report.config(state=DISABLED)

    def setStatus(self,text:str) -> None:
        """Set status bar text from other code.
        
        :param text: New content for status bar.
        :return: 
        """
        self.logger.info(text)
        self.appendReport(text)
        self.status.config(text=text)
        self.root.update_idletasks()

    def gotoWeb(self,page:str)->None:
        """Opens wiki page on GitHub.
        
        :param page: Page tag to open browser for.
        :return: 
        """
        if page=='wiki':
            webbrowser.open('http://github.com/ivan866/readTobiiGlasses/wiki')
        elif page=='repo':
            webbrowser.open('http://github.com/ivan866/readTobiiGlasses')



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--settings', help='Path to settings XML file')
    args = parser.parse_args()

    if args.settings:
        rtg = ReadTobiiGlasses(gui=False)
        rtg.logger.debug(rtg.settingsReader)
        rtg.settingsReader.select(args.settings)
        rtg.dataReader.read(rtg.settingsReader,rtg.multiData)
        rtg.stats.descriptive(rtg.multiData)
        sys.exit()
    else:
        ReadTobiiGlasses()

if __name__ == "__main__":
    main()