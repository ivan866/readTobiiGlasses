import argparse
from datetime import datetime
import webbrowser

import logging

from tkinter import *

import matplotlib
matplotlib.rcParams['backend'] = "TkAgg"

from SettingsReader import SettingsReader
from data.MultiData import MultiData
from data.PivotData import PivotData
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
        self.status.config(text='Please select settings or batch file.')
        self.status.pack(side=BOTTOM,fill=X)

        self.report=Text(self.root, bg='lightgray', relief=SUNKEN, wrap=WORD)
        self.report.insert('0.0',datetime.now().strftime('%Y-%m-%d') + '\n')
        self.appendReport('ReadTobiiGlasses started.')
        self.report.pack(side=LEFT,anchor=NW,fill=BOTH)


        #setup other classes
        self.logger.debug('instantiating classes...')
        self.settingsReader = SettingsReader(self)
        self.multiData = MultiData(self)
        self.pivotData = PivotData(self)
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
        settingsMenu.add_command(label="Run batch and pivot tables...", command=lambda: self.settingsReader.selectBatch(self.pivotData,self.stats))
        self.rootMenu.add_cascade(label="Settings", menu=settingsMenu)

        dataMenu = Menu(self.rootMenu, tearoff=0)
        dataMenu.add_command(label="Parse settings and read data", command=lambda: self.dataReader.read(self.settingsReader,self.multiData))
        dataMenu.add_command(label="Summary and validation", command=self.multiData.validate)
        dataMenu.add_command(label="Standartization", command=lambda: self.setStatus('Not implemented.'))
        exportMenu = Menu(dataMenu, tearoff=0)
        exportMenu.add_command(label="Fixations/saccades to Excel", command=lambda: self.dataExporter.exportFixations(self.multiData,'xls'))
        exportMenu.add_command(label="Fixations/saccades to CSV", command=lambda: self.dataExporter.exportFixations(self.multiData,'csv'))
        exportMenu.add_command(label="Gyroscope data", command=lambda: self.dataExporter.exportGyro(self.multiData))
        exportMenu.add_command(label="Voc/ocul combined", command=lambda: self.setStatus('Not implemented.'))
        dataMenu.add_cascade(label="Export", menu=exportMenu)
        self.rootMenu.add_cascade(label="Data", menu=dataMenu)

        statsMenu = Menu(self.rootMenu, tearoff=0)
        statsMenu.add_command(label="Descriptive", command=lambda: self.stats.descriptive(self.multiData))
        statsMenu.add_command(label="Difference", command=lambda: self.stats.difference(self.pivotData))
        statsMenu.add_command(label="Variance", command=lambda: self.setStatus('Not implemented.'))
        # экспортируем и сразу открываем
        # statsMenu.add_command(label="Save report to Excel", command=self.stats.save)
        self.rootMenu.add_cascade(label="Statistics", menu=statsMenu)

        vizMenu = Menu(self.rootMenu, tearoff=0)
        plotMenu = Menu(vizMenu, tearoff=0)
        plotMenu.add_command(label="Temporal", command=lambda: self.tempoPlot.draw(self.multiData))
        plotMenu.add_command(label="Spatial", command=lambda: self.spatialPlot.draw(self.multiData))
        plotMenu.add_command(label="Combined", command=lambda: self.combiPlot.draw(self.multiData))
        vizMenu.add_cascade(label="Plots", menu=plotMenu)
        distrMenu = Menu(vizMenu, tearoff=0)
        distrMenu.add_command(label="Histogram", command=self.stubPlot.draw)
        distrMenu.add_command(label="Density", command=self.stubPlot.draw)
        distrMenu.add_command(label="Cumulative", command=self.stubPlot.draw)
        distrMenu.add_command(label="Spectrogram", command=self.stubPlot.draw)
        vizMenu.add_cascade(label="Distribution", menu=distrMenu)
        vizMenu.add_command(label="Gaze overlay animation", command=self.stubPlot.draw)
        vizMenu.add_command(label="3D gaze vectors", command=self.stubPlot.draw)
        vizMenu.add_command(label="Heatmap", command=self.stubPlot.draw)
        vizMenu.add_command(label="Distance matrix", command=self.stubPlot.draw)
        self.rootMenu.add_cascade(label="Visualizations", menu=vizMenu)

        helpMenu = Menu(self.rootMenu, tearoff=0)
        manualsMenu = Menu(helpMenu, tearoff=0)
        manualsMenu.add_command(label="Tobii gyroscope data format", command=lambda: self.gotoWeb('glasses2API'))
        manualsMenu.add_command(label="Tobii coordinate systems", command=lambda: self.gotoWeb('coordSys'))
        helpMenu.add_cascade(label="Manuals", menu=manualsMenu)
        helpMenu.add_command(label="Repository", command=lambda: self.gotoWeb('repo'))
        helpMenu.add_command(label="Wiki", command=lambda: self.gotoWeb('wiki'))
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

    def saveReport(self,saveDir:str)->None:
        """Write current report to file.
        
        :param saveDir: Path to write into.
        :return: 
        """
        reportFile = open(saveDir + '/history.txt', 'w')
        reportFile.write(self.report.get('0.0', END))
        reportFile.close()

    def gotoWeb(self,page:str)->None:
        """Opens wiki page on GitHub.
        
        :param page: Page tag to open browser for.
        :return: 
        """
        if page=='repo':
            webbrowser.open('http://github.com/ivan866/readTobiiGlasses')
        elif page=='wiki':
            webbrowser.open('http://github.com/ivan866/readTobiiGlasses/wiki')
        elif page=='glasses2API':
            webbrowser.open('http://tobiipro.com/product-listing/tobii-pro-glasses-2-sdk/')
        elif page=='coordSys':
            webbrowser.open('http://developer.tobiipro.com/commonconcepts.html')


    def batchProcess(self,args:object,serial:bool=False,savePath:str='')->None:
        """Calls all the methods to make statistical calculations.
        
        :param args: Command line arguments object.
        :param serial: If this is a serial batch for combining reports to pivot table.
        :param savePath: Directory tree to save batch into.
        :return: 
        """
        self.logger.debug(self.settingsReader)
        self.settingsReader.select(args.settings)
        self.dataReader.read(self.settingsReader, self.multiData,serial=serial)
        self.stats.descriptive(self.multiData,serial=serial,savePath=savePath)
        if not serial:
            sys.exit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--settings', help='Path to settings XML file')
    args = parser.parse_args()

    if args.settings:
        rtg = ReadTobiiGlasses(gui=False)
        rtg.batchProcess(args,serial=False)
    else:
        ReadTobiiGlasses()

if __name__ == "__main__":
    main()