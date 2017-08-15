import argparse
from datetime import datetime

from tkinter import *

from SettingsReader import SettingsReader
from data.MultiData import MultiData
from data.DataReader import DataReader
from data.DataExporter import DataExporter
from stats.Stats import Stats
from viz.plots.GazePlot import StubPlot




class ReadTobiiGlasses():

    """Main class of the utility.
    
    Maintains top level window with menus and a status bar.
    
    """

    def __init__(self):
        """Setup application and populate menu."""
        self.root = Tk()
        self.root.geometry('640x400')
        self.root.title('Read Tobii Glasses')

        self.rootMenu = Menu(self.root)
        self.root.config(menu=self.rootMenu)


        self.status = Label(self.root, bd=1, relief=SUNKEN, anchor=W)
        self.status.config(text='Please select settings.')
        self.status.pack(side=BOTTOM,fill=X)

        self.report=Text(self.root, bg='lightgray', relief=SUNKEN, wrap=WORD)
        self.report.insert('0.0',datetime.now().strftime('%Y-%m-%d') + '\n')
        self.appendReport('ReadTobiiGlasses started.')
        self.report.pack(side=LEFT,anchor=NW,fill=BOTH)


        #setup other classes
        self.settingsReader = SettingsReader(self)
        self.multiData = MultiData(self)
        self.dataReader = DataReader(self)
        self.dataExporter = DataExporter(self)

        self.stats = Stats(self)
        self.gazePlot = StubPlot(self)


        #populate menu
        settingsMenu = Menu(self.rootMenu, tearoff=0)
        settingsMenu.add_command(label="Select...", command=self.settingsReader.select)
        settingsMenu.add_command(label="Modify in external editor", command=self.settingsReader.open)
        self.rootMenu.add_cascade(label="Settings", menu=settingsMenu)

        dataMenu = Menu(self.rootMenu, tearoff=0)
        dataMenu.add_command(label="Parse settings and read data", command=lambda: self.dataReader.read(self.settingsReader,self.multiData))
        dataMenu.add_command(label="Validation", command=self.multiData.validate)
        exportMenu = Menu(dataMenu, tearoff=0)
        exportMenu.add_command(label="Fixations to Excel", command=lambda: self.dataExporter.exportFixations(self.multiData,'xls'))
        exportMenu.add_command(label="Fixations to CSV", command=lambda: self.dataExporter.exportFixations(self.multiData,'csv'))
        exportMenu.add_command(label="Gyroscope data", command=lambda: self.dataExporter.exportGyro(self.multiData))
        dataMenu.add_cascade(label="Export", menu=exportMenu)
        self.rootMenu.add_cascade(label="Data", menu=dataMenu)

        statsMenu = Menu(self.rootMenu, tearoff=0)
        statsMenu.add_command(label="Descriptive", command=lambda: self.stats.descriptive(self.multiData))
        # экспортируем и сразу открываем
        # statsMenu.add_command(label="Save report to Excel", command=self.stats.save)
        self.rootMenu.add_cascade(label="Statistics", menu=statsMenu)

        vizMenu = Menu(self.rootMenu, tearoff=0)
        plotMenu = Menu(vizMenu, tearoff=0)
        plotMenu.add_command(label="Temporal", command=self.gazePlot.draw)
        plotMenu.add_command(label="Spatial", command=self.gazePlot.draw)
        plotMenu.add_command(label="Combined", command=self.gazePlot.draw)
        vizMenu.add_cascade(label="Plots", menu=plotMenu)
        vizMenu.add_command(label="Gaze overlay", command=self.gazePlot.draw)
        vizMenu.add_command(label="3D gaze vectors", command=self.gazePlot.draw)
        vizMenu.add_command(label="Heatmap", command=self.gazePlot.draw)
        vizMenu.add_command(label="Intersection matrix", command=self.gazePlot.draw)
        self.rootMenu.add_cascade(label="Visualizations", menu=vizMenu)


        self.root.mainloop()



    def appendReport(self,text:str) -> None:
        """Appends text to report text widget.
        
        :param text: Text to append.
        :return: 
        """
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
        self.appendReport(text)
        self.status.config(text=text)
        self.root.update_idletasks()



def main():
    rtg=ReadTobiiGlasses()

    parser = argparse.ArgumentParser()
    parser.add_argument('settings', default='', help='Path to settings XML file')
    args = parser.parse_args()

    if args.settings:
        rtg.settingsReader.select(args.settings)
        rtg.dataReader.read()
        rtg.stats.descriptive()
        rtg.stats.save()

if __name__ == "__main__":
    main()