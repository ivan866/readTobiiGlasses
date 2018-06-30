#!/usr/bin/env python
import argparse
import sys
from datetime import datetime
import webbrowser

import logging

from tkinter import *


import matplotlib
import matplotlib.pylab as pylab
matplotlib.rcParams['backend'] = "TkAgg"
matplotlib.style.use('bmh') #bmh, ggplot, seaborn, fivethirtyeight
params = {
          #'font.family': 'arial',
          'figure.figsize': (6, 6),
          #'figure.dpi': 150,
          'axes.titlesize': 'medium',
          'axes.titleweight': 'bold',
          'axes.labelsize': 'small',
          #'axes.facecolor': '#E8DDCB',
          'axes.grid': True,
          'axes.grid.which': 'major',    #both, major
          'axes.axisbelow': True,    #line, False
          #'grid.alpha': 0.8,    #line, False
          'xtick.labelsize': 'x-small',
          'ytick.labelsize': 'x-small',
          'xtick.direction': 'out',
          'ytick.direction': 'out',
          'ytick.left': True,
          'xtick.bottom': True,
          'ytick.minor.left': True,
          'xtick.minor.bottom': True,
          'xtick.minor.visible': True,
          'ytick.minor.visible': True,
          'legend.fontsize': 'xx-small',
          'legend.facecolor': 'grey',
          'hist.bins': 20,
          'boxplot.vertical': True,
          'boxplot.notch': True,
          'boxplot.showmeans': False,
          'boxplot.showcaps': True,
          'boxplot.showfliers': False,
          'boxplot.meanline': False,
          'errorbar.capsize': 9
          }
pylab.rcParams.update(params)


from SettingsReader import SettingsReader

from data.MultiData import MultiData
from data.PivotData import PivotData
from data.DataReader import DataReader
from data.DataExporter import DataExporter

from annotations import Annotations
from stats.Stats import Stats

from viz.plots.TempoPlot import TempoPlot
from viz.plots.SpatialPlot import SpatialPlot
from viz.plots.CombiPlot import CombiPlot
from viz.distribution.Spectrogram import Spectrogram
from viz.video.AviSynthPlayer import AviSynthPlayer






class ReadTobiiGlasses():

    """Main class of the utility.
    
    Maintains top level window with menus and a status bar.
    
    """


    def __init__(self,gui:bool=True):
        """Setup application and populate menu.
        
        :param gui: Whether to start gui.
        """
        #TODO switch to ?fltk GUI
        #TODO add scrollbar to report textfield
        #FIXME gui freezing while pivoting data
        #TODO command line procedure for gyro2eaf with custom arguments
        #TODO add environment setup script (setup.py), как сделать python package с манифестом пакета
        #TODO !tests and raises error coding style
		#TODO add bash script for batch
        #TODO reroute stderr to report field
        #TODO add cli equivalent commands copied to report with actual arguments
        #TODO sync package API
        self.LOG_FORMAT="%(levelname)s %(asctime)s %(pathname)s at %(lineno)s - %(message)s"
        logging.basicConfig(filename='readTobiiGlasses.log',
                            level=logging.DEBUG,
                            format=self.LOG_FORMAT)
        self.logger=logging.getLogger()

        def rerouteExceptions(type, value, traceback):
            self.logger.exception("{0}, {1}, {2}".format(str(type), str(value), str(traceback)))
        #TODO
        #sys.excepthook = rerouteExceptions


        self.PROJECT_NAME='Read Tobii Glasses'
        self.PROJECT_NAME_SHORT='RTG'
        self.GAZE_COMPONENTS_LIST=['fixations','saccades','eyesNotFounds','unclassifieds',"imu","gyro","accel"]
        self.VIDEO_FRAMERATE=100
        self.PYPER_MANU_ARGS=[128,100,2000,1000,'manu_output']
        self.logger.debug('creating tk root..')
        self.root = Tk()
        self.root.geometry('640x400')
        self.root.title(self.PROJECT_NAME)

        self.rootMenu = Menu(self.root)
        self.root.config(menu=self.rootMenu)


        self.logger.debug('creating report and status widgets...')
        self.status = Label(self.root, bd=1, relief=RIDGE, anchor=W)
        self.status.config(text='Please select settings or batch file.')
        self.status.pack(side=BOTTOM,fill=X)

        self.report=Text(self.root, bg='lightgray', relief=SUNKEN, wrap=CHAR)
        self.report.insert('1.0',datetime.now().strftime('%Y-%m-%d') + '\n')
        self.report_line_num=1
        self.appendReport('ReadTobiiGlasses started.')
        self.appendReport('Interactive GUI session.')
        self.report.pack(side=LEFT,anchor=NW,fill=BOTH)


        #setup other classes
        self.logger.debug('instantiating classes...')
        self.settingsReader = SettingsReader(self)

        self.multiData = MultiData(self)
        self.pivotData = PivotData(self)
        self.dataReader = DataReader(self)
        self.dataExporter = DataExporter(self)

        self.stats = Stats(self)

        self.tempoPlot = TempoPlot(self)
        self.spatialPlot = SpatialPlot(self)
        self.combiPlot = CombiPlot(self)
        self.spectrogram = Spectrogram(self)

        self.aviSynthPlayer = AviSynthPlayer()


        self.logger.debug('populating menus...')
        #populate menu
        #FIXME all commands refactor to Command pattern
        settingsMenu = Menu(self.rootMenu, tearoff=0)
        settingsMenu.add_command(label="Select...", command=self.settingsReader.select)
        settingsMenu.add_command(label="Edit...", command=self.settingsReader.open)
        settingsMenu.add_command(label="Run batch and pivot tables...", command=lambda: self.settingsReader.selectBatch(self.pivotData,self.stats,dataReader=self.dataReader,multiData=self.multiData), state=DISABLED)
        self.rootMenu.add_cascade(label="Settings", menu=settingsMenu)


        dataMenu = Menu(self.rootMenu, tearoff=0)
        dataMenu.add_command(label="Parse settings and read data", command=lambda: self.dataReader.read(self.settingsReader,self.multiData))
        dataMenu.add_command(label="Summary and validation", command=self.multiData.validate)
        dataMenu.add_command(label="Standartization", command=lambda: self.setStatus('Not implemented.'), state=DISABLED)
        exportMenu = Menu(dataMenu, tearoff=0)
        exportMenu.add_command(label="Fixations/saccades to CSV", command=lambda: self.dataExporter.exportFixations(self.multiData,'csv'))
        exportMenu.add_command(label="Fixations/saccades to Excel", command=lambda: self.dataExporter.exportFixations(self.multiData,'xls'))
        exportMenu.add_command(label="Gyroscope/accelerometer to CSV", command=lambda: self.dataExporter.exportGyro(self.multiData))
        exportMenu.add_command(label="All tables to CSV", command=lambda: self.dataExporter.exportCSV(self.multiData))
        exportMenu.add_command(label="All tables to Excel", command=lambda: self.dataExporter.exportCSV(self.multiData, format='xlsx'))
        exportMenu.add_command(label="All tables to SQL", command=lambda: self.dataExporter.exportSQL(self.multiData))
        dataMenu.add_cascade(label="Export", menu=exportMenu)
        self.rootMenu.add_cascade(label="Data", menu=dataMenu)

        annotationMenu = Menu(self.rootMenu, tearoff=0)
        annotationMenu.add_command(label="Sanity check", command=lambda: self.setStatus('Not implemented.'), state=DISABLED)
        annotationMenu.add_command(label="Detect ceph motions (gyro)", command=lambda: Annotations.imuToEaf(self, self.multiData,settingsReader=self.settingsReader,dataExporter=self.dataExporter))
        annotationMenu.add_command(label="Detect manu motions (pyper)", command=lambda: Annotations.callPyper(self, self.multiData,settingsReader=self.settingsReader,dataExporter=self.dataExporter, args=self.PYPER_MANU_ARGS))
        annotationMenu.add_command(label="Convert pyper CSV to EAF", command=lambda: Annotations.pyperToEaf(self, self.multiData,settingsReader=self.settingsReader,dataExporter=self.dataExporter))
        annotationMenu.add_command(label="Motion detection quality assessment", command=lambda: Annotations.qualityAssessment(self, self.multiData,settingsReader=self.settingsReader,dataExporter=self.dataExporter))
        annotationMenu.add_command(label="Voc/ocul transcript", command=lambda: self.setStatus('Not implemented.'))
        self.rootMenu.add_cascade(label="Annotation", menu=annotationMenu)

        searchMenu = Menu(self.rootMenu, tearoff=0)
        gazeMenu = Menu(searchMenu, tearoff=0)
        gazeMenu.add_command(label="All saccades", command=lambda: self.setStatus('Not implemented.'))
        gazeMenu.add_command(label="Tracking lost", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Gaze", menu=gazeMenu)
        vocMenu = Menu(searchMenu, tearoff=0)
        vocMenu.add_command(label="Descending tone", command=lambda: self.setStatus('Not implemented.'))
        vocMenu.add_command(label="Descending-ascending tone", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Vocal", menu=vocMenu)
        manuMenu = Menu(searchMenu, tearoff=0)
        manuMenu.add_command(label="Retraction, no preparation", command=lambda: self.setStatus('Not implemented.'))
        manuMenu.add_command(label="P-S-R", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Manual", menu=manuMenu)
        cephMenu = Menu(searchMenu, tearoff=0)
        cephMenu.add_command(label="Upwards movement", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Cephalic", menu=cephMenu)
        oculMenu = Menu(searchMenu, tearoff=0)
        oculMenu.add_command(label="Face/hands", command=lambda: self.setStatus('Not implemented.'))
        oculMenu.add_command(label="N, following R, following C", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Ocular", menu=oculMenu)
        boolMenu = Menu(searchMenu, tearoff=0)
        boolMenu.add_command(label="Union...", command=lambda: self.setStatus('Not implemented.'))
        boolMenu.add_command(label="Intersection...", command=lambda: self.setStatus('Not implemented.'))
        boolMenu.add_command(label="Difference...", command=lambda: self.setStatus('Not implemented.'))
        searchMenu.add_cascade(label="Boolean", menu=boolMenu)
        searchMenu.add_command(label="Execute SQL query", command=lambda: self.setStatus('Not implemented.'))
        self.rootMenu.add_cascade(label="Search", menu=searchMenu)

        statsMenu = Menu(self.rootMenu, tearoff=0)
        statsMenu.add_command(label="Descriptive",
                              command=lambda: self.stats.descriptive(self.multiData, dataExporter=self.dataExporter))
        statsMenu.add_command(label="Difference", command=lambda: self.stats.difference(self.pivotData))
        statsMenu.add_command(label="ANOVA", command=lambda: self.stats.ANOVA_stats(self.multiData, self.pivotData, dataExporter=self.dataExporter))
        # statsMenu.add_command(label="Save report to Excel", command=self.stats.save)
        self.rootMenu.add_cascade(label="Statistic", menu=statsMenu)

        vizMenu = Menu(self.rootMenu, tearoff=0)
        plotMenu = Menu(vizMenu, tearoff=0)
        plotMenu.add_command(label="Temporal", command=lambda: self.tempoPlot.drawByIntervals(self.multiData))
        plotMenu.add_command(label="Spatial", command=lambda: self.spatialPlot.drawByIntervals(self.multiData))
        plotMenu.add_command(label="Combined", command=lambda: self.combiPlot.drawByIntervals(self.multiData))
        vizMenu.add_cascade(label="Plot", menu=plotMenu)
        distrMenu = Menu(vizMenu, tearoff=0)
        distrMenu.add_command(label="Histogram", command=lambda: self.setStatus('Not implemented.'))
        distrMenu.add_command(label="Density", command=lambda: self.setStatus('Not implemented.'))
        distrMenu.add_command(label="Cumulative", command=lambda: self.setStatus('Not implemented.'))
        distrMenu.add_command(label="Spectrogram", command=lambda: self.spectrogram.drawByIntervals(self.multiData), state=DISABLED)
        vizMenu.add_cascade(label="Distribution", menu=distrMenu)
        videoMenu = Menu(vizMenu, tearoff=0)
        videoMenu.add_command(label="AviSynth player", command=lambda: self.aviSynthPlayer.launchAVS(self.settingsReader))
        videoMenu.add_command(label="Gaze point overlay", command=lambda: self.setStatus('Not implemented.'))
        videoMenu.add_command(label="Investigate sync tags", command=lambda: self.setStatus('Not implemented.'))
        videoMenu.add_command(label="Montage single video...", command=lambda: self.setStatus('Not implemented.'))
        vizMenu.add_cascade(label="Video", menu=videoMenu)
        vizMenu.add_command(label="Heatmap", command=lambda: self.setStatus('Not implemented.'), state=DISABLED)
        vizMenu.add_command(label="Distance matrix", command=lambda: self.setStatus('Not implemented.'))
        vizMenu.add_command(label="3D scene reconstruction", command=lambda: self.setStatus('Not implemented.'), state=DISABLED)
        self.rootMenu.add_cascade(label="Media", menu=vizMenu)


        helpMenu = Menu(self.rootMenu, tearoff=0)
        manualsMenu = Menu(helpMenu, tearoff=0)
        manualsMenu.add_command(label="Tobii coordinate systems", command=lambda: self.gotoWeb('coordSys'))
        manualsMenu.add_command(label="Tobii gyroscope data format", command=lambda: self.gotoWeb('glasses2API'))
        manualsMenu.add_command(label="JAI Go camera", command=lambda: self.gotoWeb('jaiCameras'))
        helpMenu.add_cascade(label="Manuals", menu=manualsMenu)
        helpMenu.add_command(label="FAQ", command=lambda: self.gotoWeb('FAQ'))
        helpMenu.add_command(label="Wiki", command=lambda: self.gotoWeb('wiki'))
        helpMenu.add_command(label="Repository", command=lambda: self.gotoWeb('repo'))
        helpMenu.add_command(label="Submit a bug...", command=lambda: self.gotoWeb('bugs'))
        self.rootMenu.add_cascade(label="Help", menu=helpMenu)

        self.logger.debug('starting tk main loop...')
        if gui:
            self.root.mainloop()



    def appendReport(self,text:str,color:str='#000000') -> None:
        """Appends text to report text widget.
        
        :param text: Text to append.
        :param color: text color, useful for warnings and successful operations.
        :return: 
        """
        #TODO whether to include 'now' timecode - method argument
        self.report_line_num=self.report_line_num+1
        now = datetime.now().strftime('%H:%M:%S')
        startIndex='{0}.{1}'.format(self.report_line_num, len(now)+1)
        endIndex='{0}.end'.format(self.report_line_num)

        if 'error' in text.lower() or 'unknown' in text.lower() or 'fail' in text.lower() or 'there is no' in text.lower() or color=='error':
            color='#FF0000'
        elif 'warn' in text.lower() or color=='warning':
            color='#CC4400'
        elif 'success' in text.lower() or 'complete' in text.lower() or color=='success':
            color='#006600'
        #TODO ? can add font style for different messages
        #TODO add binding to text to open stat reports

        self.report.config(state=NORMAL)
        self.report.insert(END,now+' '+text+'\n')
        self.report.tag_add('line_'+str(self.report_line_num),startIndex,endIndex)
        self.report.tag_config('line_'+str(self.report_line_num),foreground=color)
        self.report.see(END)
        self.report.config(state=DISABLED)

    def setStatus(self,text:str,color:str='#000000') -> None:
        """Set status bar text from other code.
        
        :param text: New content for status bar.
        :param color: text color (passed to report field).
        :return: 
        """
        #TODO progress vertical bar rotating in text field
        self.logger.info(text)
        self.appendReport(text,color=color)
        self.status.config(text=text)
        self.root.update_idletasks()

    def reportError(self)->None:
        """Prints current Exception info to report field.

        :return: None.
        """
        eInfo = sys.exc_info()
        self.appendReport('{0}: {1}.'.format(eInfo[0].__name__, eInfo[1]),color='error')


    def saveReport(self,saveDir:str)->None:
        """Write current report to file.
        
        :param saveDir: Path to write into.
        :return: 
        """
        reportFile = open(saveDir + '/history.txt', 'w')
        reportFile.write(self.report.get('0.0', END))
        reportFile.close()


    #TODO add JAI camera SDK website
    def gotoWeb(self,page:str)->None:
        """Opens wiki page on GitHub.
        
        :param page: Page tag to open browser for.
        :return: 
        """
        if page=='repo':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses')
        elif page=='FAQ':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/wikis/FAQ')
        elif page=='wiki':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/wikis')
        elif page=='bugs':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/issues/new')
        elif page=='glasses2API':
            webbrowser.open('http://tobiipro.com/product-listing/tobii-pro-glasses-2-sdk/')
        elif page=='coordSys':
            webbrowser.open('http://developer.tobiipro.com/commonconcepts.html')
        elif page=='jaiCameras':
            webbrowser.open('https://stemmer-imaging.co.uk/en/products/series/jai-go/')
        else:
            self.setStatus('Unknown URL.')




    def CLIProcess(self, args:object, serial:bool=False, savePath:str='')->None:
        """Calls all the functions specified in command line arguments.

        :param args: Command line arguments object.
        :param serial: If this is a serial batch for combining reports to pivot table.
        :param savePath: Directory tree to save batch into.
        :param functions: list of functions to perform with specified settings or batch
        :return:
        """
        if 'desc_stats' in args.functions:
            self.stats.descriptive(self.multiData,dataExporter=self.dataExporter,serial=serial,savePath=savePath)
        if 'detect_ceph' in args.functions:
            if args.ceph_engine == 'gyro':
                Annotations.imuToEaf(self, self.multiData, settingsReader=self.settingsReader,dataExporter=self.dataExporter)
            elif args.ceph_engine == 'eavise':
                self.setStatus('Not implemented.')
        if 'detect_manu' in args.functions:
            if args.manu_engine=='green_people':
                self.setStatus('Not implemented.')
            elif args.manu_engine=='pyper':
                Annotations.callPyper(self, self.multiData, settingsReader=self.settingsReader, dataExporter=self.dataExporter, args=args.manu_args)
            elif args.manu_engine == 'ssd':
                self.setStatus('Not implemented.')

        if not serial:
            sys.exit()




#TODO change args in wiki on github
#TODO CLI with settings arg only should load and parse them
def main():
    #TODO if manu engine specified, args should be present
    parser = argparse.ArgumentParser(description='Launch ReadTobiiGlasses from the command line.')
    settingsFileGroup = parser.add_mutually_exclusive_group()
    settingsFileGroup.add_argument('-s', '--settings-file', type=str, help='Path to settings XML file.')
    #settingsFileGroup.add_argument('-b', '--batch-file', type=str, help='Path to batch file - to process several settings paths, executing the next specified options on each.')

    parser.add_argument('--desc-stats', action='append_const', dest='functions', const='desc_stats', help='Calculate descriptive statistics and save detailed report.')

    cephGroup = parser.add_argument_group('ceph', 'Parameters which apply to ceph annotations.')
    cephGroup.add_argument('--detect-ceph', action='append_const', dest='functions', const='detect_ceph', help='Export gyroscope to ELAN.')
    cephGroup.add_argument('--ceph-engine', type=str, choices=['gyro', 'eavise', 'winanalyze'], default='gyro', help='Source of data for ceph motion detection.')
    cephGroup.add_argument('--ceph-args', nargs='+', default=[128,100,2000,1000,'manu_output'], help='Parameters for the algorithm used for ceph motion detection.')

    manuGroup = parser.add_argument_group('manu', 'Parameters which apply to manu annotations.')
    manuGroup.add_argument('--detect-manu', action='append_const', dest='functions', const='detect_manu', help='Perform manu motion detection.')
    manuGroup.add_argument('--manu-engine', type=str, choices=['green_people', 'pyper', 'tracktor', 'winanalyze', 'ssd'], default='pyper', help='Script or tool to use for manu motion tracking.')
    #TODO default args copy
    manuGroup.add_argument('--manu-args', nargs='+', default=[128,100,2000,1000,'annot'], help='Parameters for the manu CLI tool, e.g. threshold, etc.')
    args = parser.parse_args()

    #with or without command line parameters
    #FIXME если в командной строке указан только файл настроек, какая это сессия считается?
    if args.settings_file:# or args.batch_file:
        rtg = ReadTobiiGlasses(gui=False)
        rtg.appendReport('Using CLI with args: {0}.'.format(print(args)))
        if args.settings_file:
            serial = False
            rtg.settingsReader.select(args.settings_file)
            rtg.dataReader.read(rtg.settingsReader, rtg.multiData, serial=serial)
            rtg.CLIProcess(args=args, serial=serial)
        #elif args.batch_file:
        #    self.settingsReader.selectBatch(pivotData=self.pivotData, stats=self.stats, file=args.batch_file)
    else:
        ReadTobiiGlasses()

if __name__ == "__main__":
    main()