import os
import subprocess
from datetime import timedelta

import xml.etree.ElementTree as ET

from tkinter import filedialog

from data import Utils



class SettingsReader:

    """Reads, parses and queries xml file with settings."""

    readers=[]


    def __init__(self,topWindow):
        self.topWindow=topWindow
        self.dataDir = None
        self.settingsFile = None
        self.settingsTree = None
        self.settings = None
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

        self.dataDir=os.path.dirname(self.settingsFile)
        self.topWindow.setStatus('Settings file selected (not read or modified yet).')


    def read(self)->None:
        """Actually reads and parses xml file contents."""
        self.settingsTree = ET.parse(self.settingsFile)
        self.settings = self.settingsTree.getroot()
        self.topWindow.setStatus('Settings parsed ('+self.settingsFile+').')

        #TODO if no intervals
        if len(self.getIntervals()) == 0:
            self.topWindow.setStatus('No intervals specified. Assuming monolythic data.')


    def open(self) -> None:
        """Asynchronously opens settings in external text editor."""
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

    def getTypeById(self,type:str,id:str) -> object:
        """Filters settings nodes by both type and id.
        
        :param type: type string from settings.
        :param id: id string from settings.
        :return: ElementTree.Element
        """
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
        return self.settings.find("interval[@id='"+id+"']")

    def getIntervals(self) -> list:
        """Returns all intervals.
        
        :return: A list of interval nodes from settings.
        """
        return self.settings.findall("interval")


    def getStartTimeById(self,id:str,format:bool=False) -> object:
        """Computes and returns start time of interval specified by its id.
        
        Based on start time and durations of previous intervals.
        
        :param id: id attribute of interval.
        :param format: bool whether to convert time to str or not.
        :return: Start time of interval in timedelta object.
        """
        ints=self.getIntervals()
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



    def check(self) -> bool:
        """Returns True if settings are already read, False otherwise.
        
        :return: A bool representing presence of settings data in memory.
        """
        if self.settings:
            return True
        else:
            self.topWindow.setStatus('Read settings and data first.')
            return False