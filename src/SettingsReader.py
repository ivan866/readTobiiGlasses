import argparse
import os
import shutil
import re
import subprocess
from datetime import datetime

import xml.etree.ElementTree as ET

from tkinter import filedialog

import numpy
import pandas

from data import Utils



class SettingsReader:

    """Reads, parses and queries xml file with settings."""

    readers=[]


    def __init__(self,topWindow):
        #TODO refactor to singleton pattern
        self.topWindow=topWindow

        self.dataDir = None
        self.settingsFile = None
        self.settingsTree = None
        self.settings = None

        self.batchNum=0
        self.batchFile=None
        self.batchDir=None
        self.batchSettingsTree = None
        self.batchSettings=None

        SettingsReader.readers.append(self)


    @classmethod
    def getReader(cls, i:int=0) -> object:
        """Statically iterates through all settings readers.
        
        Makes reader available to code globally.
        
        :param i: Index of needed reader.
        :return: None
        """
        return cls.readers[i]


    def select(self, file:str=None) -> None:
        """Selects file with settings, either via dialogue or literally by path string.
        
        :param file: Path string. Used when running through terminal.
        :return: None
        """
        if not file:
            self.settingsFile = filedialog.askopenfilename(filetypes = (("eXtensible Markup Language","*.xml"),("all files","*.*")))
        else:
            self.settingsFile=file

        if self.settingsFile:
            self.dataDir=os.path.dirname(self.settingsFile)
            self.topWindow.setStatus('Settings file selected (not read or modified yet).')

    def selectBatch(self,pivotData:object,stats:object)-> None:
        """Parses .bat file and runs every script with every settings file in it. Then combines reports together for summary statistic analysis.
        
        :param pivotData: PivotData object to hold tables into.
        :param stats: Stats object to write files with.
        :return: 
        """
        batchFile = filedialog.askopenfilename(filetypes = (("Batch command file","*.bat"),("all files","*.*")))

        if batchFile:
            #обнуляем на случай повторного запуска в той же сессии
            self.batchNum = 0
            self.batchFile=batchFile
            self.batchSettingsTree=None
            self.readBatch(pivotData=pivotData,stats=stats)

    def read(self,serial:bool=False)->None:
        """Actually reads and parses xml file contents.
        
        :param serial: If this is a serial batch.
        :return: 
        """
        self.topWindow.logger.debug('reading settings...')
        self.settingsTree = ET.parse(self.settingsFile)
        self.settings = self.settingsTree.getroot()
        if serial:
            for el in self.settings.findall('*'):
                el.set('batchNum', str(self.batchNum))
        #init of batch settings tree
        if not self.batchSettingsTree:
            self.batchSettingsTree=self.settingsTree
            self.batchSettings=self.batchSettingsTree.getroot()
        else:
            self.batchSettings.extend(self.settings)

        self.topWindow.setStatus('Settings parsed ('+self.settingsFile+').')

        if len(self.getIntervals()) == 0:
            self.topWindow.setStatus('No intervals specified. Please explicitly specify at least 1 interval in settings file.')


    def readBatch(self,pivotData:object,stats:object)->None:
        """Reads and executes runs from batch sequentially.
        
        :param pivotData:
        :param stats:
        :return: 
        """
        self.topWindow.setStatus('Batch file specified. Working (REM lines not ignored)...')
        now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
        self.batchDir = os.getcwd() + '/batch_' + now
        with open(self.batchFile) as f:
            line = f.readline()
            while line:
                args = argparse.Namespace()
                args.settings = re.search('--settings=(.+)', line).groups()[0]
                self.batchNum=self.batchNum+1
                savePath = self.batchDir + '/' + str(self.batchNum)
                self.topWindow.setStatus('--Line ' + str(self.batchNum)+'--')
                self.topWindow.batchProcess(args, serial=True, savePath=savePath)
                line = f.readline()

        pivotData.pivot(settingsReader=self,stats=stats)

        self.saveSerial()
        shutil.copy2(self.batchFile, self.batchDir + '/' + os.path.basename(self.batchFile))
        self.topWindow.setStatus('Batch complete. Pivot tables ready.')
        self.topWindow.saveReport(self.batchDir)


    def open(self) -> None:
        """Asynchronously opens settings in external text editor."""
		#TODO check OS type
        self.topWindow.setStatus('Calling external editor...')
        subprocess.run('npp/notepad++.exe '+self.settingsFile)
        self.topWindow.setStatus('Returned from external editor.')



    #data filtering functions
    #data files
    def getIds(self,id:str) -> list:
        """Queries settings for nodes with particular id attribute.
        
        :param id: id string from settings.
        :return: A list of matches with this id.
        """
        return self.settings.findall("file[@id='"+id+"']")

    def getTypes(self,type:str) -> list:
        """Returns all nodes from settings with this type attribute.
        
        :param type: type string from settings.
        :return: A list of file tags by type.
        """
        return self.settings.findall("file[@type='"+type+"']")

    def unique(self,element:str='file',field:str='',serial:bool=False)->list:
        """Filters all specified elements by field and returns unique.
        
        :param element: On what element of setings to filter on.
        :param field: For what field to serahc for.
        :param serial: Whether to search in batch settings.
        :return: List of unique fields in these elements.
        """
        if serial:
            elements=self.batchSettings.findall(element)
        else:
            elements = self.settings.findall(element)
        l=[]
        for el in elements:
            l.append(el.get(field))
        return numpy.unique(l)

    def getTypeById(self,type:str,id:str,serial:bool=False) -> object:
        """Filters settings nodes by both type and id.
        
        :param type: type string from settings.
        :param id: id string from settings.
        :param serial: Whether to find all nodes with this type/id combination. Useful for serial batch.
        :return: ElementTree.Element or list of them.
        """
        self.topWindow.logger.debug('get type by id')
        if serial:
            return self.batchSettings.findall("file[@type='" + type + "'][@id='" + id + "']")
        else:
            return self.settings.find("file[@type='" + type + "'][@id='"+id+"']")

    def getZeroTimeById(self,type:str,id:str,parse:bool=True) -> object:
        """Resolves and returns zeroTime attribute of a file tag.
        
        :param type: type string from settings.
        :param id: id string from settings.
        :param parse: bool whether to parse str to timedelta or not.
        :return: zeroTime attribute in timedelta or str format, 0 or '0' if zeroTime attribute not present.
        """
        file=self.getTypeById(type,id)
        zeroTime=file.get('zeroTime',default='0')
        if len(self.getTypes(zeroTime)):
            zeroTime=self.getTypeById(zeroTime,id).get('zeroTime')

        if parse:
            return Utils.parseTime(zeroTime)
        else:
            return zeroTime


    #intervals
    def getIntervalById(self,id:str) -> object:
        """Returns interval with particular id attribute.
        
        :param id: id string from interval.
        :return: ElementTree.Element
        """
        self.topWindow.logger.debug('get interval by id')
        return self.settings.find("interval[@id='"+id+"']")

    def getIntervals(self,ignoreEmpty:bool=True) -> list:
        """Returns all intervals.
        
        :param ignoreEmpty: Whether to cut off the empty intervals.
        :return: A list of interval nodes from settings.
        """
        if ignoreEmpty:
            return [interval for interval in self.settings.findall("interval") if interval.get('id')]
        else:
            return self.settings.findall("interval")


    def getStartTimeById(self,id:str,format:bool=False) -> object:
        """Computes and returns start time of interval specified by its id.
        
        Based on start time and durations of previous intervals.
        
        :param id: id attribute of interval.
        :param format: bool whether to convert time to str or not.
        :return: Start time of interval in timedelta object.
        """
        self.topWindow.logger.debug('get start time by id')
        ints=self.getIntervals(ignoreEmpty=False)
        startTime=Utils.parseTime(0)
        thisId=None
        for i in ints:
            thisId = i.get('id')
            if thisId==id:
                break
            duration = self.getDurationById(thisId)
            startTime = startTime + duration

        if format:
            return str(startTime)
        else:
            return startTime

    def getEndTimeById(self,id:str,format:bool=False) -> object:
        """Computes and returns end time of interval specified by its id.
        
        Based on start time and duration of given interval.
        
        :param id: id attribute of interval.
        :param format: bool whether to convert time to str or not.
        :return: End time of interval in timedelta object.
        """
        endTime=self.getStartTimeById(id)+self.getDurationById(id)
        if format:
            return str(endTime)
        else:
            return endTime


    def getDurationById(self,id:str,parse:bool=True) -> object:
        """Returns duration of interval with this id.
        
        :param id: id attribute of interval.
        :param parse: bool whether to parse str to timedelta or not.
        :return: Duration of interval in timedelta or str format.
        """
        dur=self.getIntervalById(id).get('duration')
        if parse:
            return Utils.parseTime(dur)
        else:
            return dur

    def getDurations(self,parse:bool=True)->list:
        """Returns a list of durations of all intervals.
        
        :param parse: bool whether to parse list items to timedelta or not.
        :return: A list.
        """
        durs = []
        for interval in self.getIntervals():
            durs.append(self.getDurationById(interval.get('id'),parse))
        return durs

    def totalDuration(self,parse:bool=True)->object:
        """Returns total duration of all intervals.
        
        :param parse: bool whether to parse str to timedelta or not.
        :return: Duration of interval in timedelta or str format.
        """
        dur=pandas.DataFrame(self.getDurations(True)).sum()[0]
        if parse:
            return dur
        else:
            return dur.strftime('%M:%S.%f')


    def check(self) -> bool:
        """Returns True if settings are already selected, False otherwise.
        
        :return: A bool representing presence of settings file path.
        """
        self.topWindow.logger.debug('check settings')
        if self.settingsFile:
            return True
        else:
            self.topWindow.setStatus('Select settings first!')
            return False


    def save(self,saveDir:str)->None:
        """Write current settings to file.
        
        :param saveDir: Path to write into.
        :return: 
        """
        self.topWindow.logger.debug('writing settings...')
        self.settingsTree.write(saveDir + '/' + os.path.basename(self.settingsFile))

    def saveSerial(self,saveDir:str='')->None:
        """Writes combined settings to xml file.
        
        :param saveDir: Path to save combined batch settings into.
        :return: 
        """
        if not saveDir:
            saveDir=self.batchDir
        self.batchSettingsTree.write(saveDir + '/readTobiiGlassesSettings-'+os.path.splitext(os.path.basename(self.batchFile))[0]+'.xml')