import argparse
import os
import platform
import hashlib
import shutil
import re
import subprocess
from datetime import datetime

import xml
import xml.etree.ElementTree as ET

from tkinter import filedialog


import numpy as np

import pandas as pd


from data import Utils



#TODO check when multiple intervals have empty ids
class XMLSettings:

    """Reads, parses and queries xml file with settings."""

    def __init__(self):
        self.wd = None
        self.path = None

        self.xml_tree = None
        self.xml = None

        self.channels = {}
        self.subjects = {}
        self.records = {}







    def select(self, file:str=None) -> None:
        """Selects file with settings, either via dialogue or literally by path string.
        
        :param file: Path string. Used when running through terminal.
        :return: None
        """
        if not file:
            self.path = filedialog.askopenfilename(filetypes = (("eXtensible Markup Language", "*.xml"), ("all files", "*.*")))
        else:
            self.path=file

        if self.path:
            #TODO check selected file type
            self.wd=os.path.dirname(self.path)
            #TODO add watchdog when file modified - reread data
            self.status_cb('Settings file selected (not read or modified yet).')
        else:
            self.status_cb('WARNING: Nothing selected. Please retry or choose different menu item.')
            
            
    def edit(self) -> None:
        """Asynchronously opens settings in external text editor."""
        if self.check():
            name=platform.system().lower()
            if 'windows' in name:
                self.status_cb('Calling Notepad...')
                subprocess.run('notepad ' + self.path)
            elif 'linux' in name:
                try:
                    self.status_cb('Calling gedit...')
                    subprocess.run('gedit ' + self.path)
                except CalledProcessError:
                    try:
                        self.status_cb('Calling Kate...')
                        subprocess.run('kate ' + self.path)
                    except CalledProcessError:
                        try:
                            self.status_cb('Not found. Fall back to vi...')
                            subprocess.run('vi ' + self.path)
                        except CalledProcessError:
                            self.status_cb('Not found. Abort.')
                            return None
            elif 'darwin' in name:
                self.status_cb('Calling default text editor...')
                subprocess.run('open -e ' + self.path)
            self.status_cb('Returned from editor.')





    def read(self) -> None:
        """Actually reads and parses xml file contents.
        
        :return:
        """
        #TODO check XML validity
        try:
            self.xml_tree = ET.parse(self.path)
            self.xml = self.xml_tree.getroot()
        except xml.etree.ElementTree.ParseError:
            self.error_cb()
            self.status_cb('ERROR: Bad settings file. Check your XML is valid.')
            return None
        except:
            self.error_cb()
            self.status_cb('ERROR: Parsing settings failed. Abort.')
            return None

        self.status_cb('Settings parsed ({0}).'.format(self.path), color='success')














    #data filtering functions
    #data files
    def genTypeFile(self,type:str)->object:
        """Generator of ids of particular type present in settings.

        :param channel:
        :return: File XML element from settings, if such file exists on disk.
        """
        found=False
        if self.check(full=True):
            for elem in self.getTypes(type):
                file= self.wd + '/' + elem.get('path')
                if os.path.exists(file):
                    if not found:
                        self.status_cb('Reading {0} data...'.format(type))
                        found=True
                    #добавляем контрольную сумму в настройки
                    elem.set('md5', self.md5(file))
                    yield elem
                else:
                    self.status_cb('WARNING: File specified in settings (' + os.path.basename(file) + ') does not exist!')

    def substGazeRelatedChannels(self,channel:str)->str:
        """Substitutes gaze related possible channel names to 'gaze', which should be the name of the source file type channel in settings.

        :param channel: gaze related channel name, like fixations or gyro.
        :return: 'gaze' or, in case of not related channel given, returns the argument unchanged.
        """
        if channel == 'fixations' or channel == 'saccades' or channel == 'eyesNotFounds' or channel == 'unclassifieds' or channel == "imu" or channel == "gyro" or channel == "accel":
            return 'gaze'
        else:
            return channel


    def getIds(self,id:str) -> list:
        """Queries settings for nodes with particular id attribute.
        
        :param id: id string from settings.
        :return: A list of matches with this id.
        """
        return self.xml.findall("file[@id='" + id + "']")

    def getTypes(self,type:str) -> list:
        """Returns all nodes from settings with this type attribute.
        
        :param type: type string from settings.
        :return: A list of file tags by type.
        """
        return self.xml.findall("file[@type='" + type + "']")

    def unique(self,element:str='file',field:str='',serial:bool=False)->list:
        """Filters all specified elements by field and returns unique.
        
        :param element: On what element of settings to filter on.
        :param field: For what field to search for.
        :param serial: Whether to search in batch settings.
        :return: List of unique fields in these elements.
        """
        if serial:
            elements=self.batchSettings.findall(element)
        else:
            elements = self.xml.findall(element)
        l=[]
        for el in elements:
            l.append(el.get(field))
        return np.unique(l)


    def getPathAttrById(self, type:str, id:str, absolute:bool=False) -> str:
        """Returns path of a file suitable as a record tag.

        Except it still contains type and id tags.

        :param type: type str from settings.
        :param id: id str from settings.
        :param absolute: whether to concatenate with a dataDir and leave extension.
        :return: path str.
        """
        #FIXME где уже была использована эта функция, но без учета absolute
        typeZeroName=self.substGazeRelatedChannels(type)
        file=self.getTypeById(typeZeroName,id)
        path=file.get('path')
        if absolute:
            return self.wd + '/' + path
        else:
            return os.path.splitext(path)[0]



    def getTypeById(self,type:str,id:str,serial:bool=False) -> object:
        """Filters settings nodes by both type and id.
        
        :param type: type string from settings.
        :param id: id string from settings.
        :param serial: Whether to find all nodes with this type/id combination. Useful for serial batch.
        :return: ElementTree.Element or list of them.
        """
        self.top_window.logger.debug('get type by id')
        if serial:
            return self.batchSettings.findall("file[@type='" + type + "'][@id='" + id + "']")
        else:
            return self.xml.find("file[@type='" + type + "'][@id='" + id + "']")

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
        self.top_window.logger.debug('get interval by id')
        return self.xml.find("interval[@id='" + id + "']")

    def getIntervals(self,ignoreEmpty:bool=True) -> list:
        """Returns all intervals.
        
        :param ignoreEmpty: Whether to cut off the empty and utility intervals.
        :return: A list of interval nodes from settings.
        """
        if ignoreEmpty:
            return [interval for interval in self.xml.findall("interval") if interval.get('id') and '_' not in interval.get('id')[0]]
        else:
            return self.xml.findall("interval")


    def getStartTimeById(self,id:str,format:bool=False) -> object:
        """Computes and returns start time of interval specified by its id.
        
        Based on start time and durations of previous intervals.
        
        :param id: id attribute of interval.
        :param format: bool whether to convert time to str or not.
        :return: Start time of interval in timedelta object.
        """
        self.top_window.logger.debug('get start time by id')
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
        for interval in self.getIntervals(ignoreEmpty=True):
            durs.append(self.getDurationById(interval.get('id'),parse))
        return durs

    def totalDuration(self,parse:bool=True)->object:
        """Returns total duration of all intervals.
        
        :param parse: bool whether to parse str to timedelta or not.
        :return: Duration of interval in timedelta or str format.
        """
        dur=pd.DataFrame(self.getDurations(True)).sum()[0]
        if parse:
            return dur
        else:
            return dur.strftime('%M:%S.%f')



    def check(self,full:bool=False) -> bool:
        """Returns True if settings are already selected, False otherwise.

        :param full: if to check settings actually read and parsed already.
        :return: A bool representing presence of settings file path.
        """
        self.top_window.logger.debug('check settings')
        if not full:
            if self.path:
                return True
            else:
                self.status_cb('WARNING: Select settings first!')
                return False
        else:
            if self.xml:
                return True
            else:
                self.status_cb('WARNING: Read and parse settings first!')
                return False


    def save(self,saveDir:str)->None:
        """Write current settings to file.
        
        :param saveDir: Path to write into.
        :return: 
        """
        self.top_window.logger.debug('writing settings...')
        self.xml_tree.write(saveDir + '/' + os.path.basename(self.path))

    def saveSerial(self,saveDir:str='')->None:
        """Writes combined settings to xml file.
        
        :param saveDir: Path to save combined batch settings into.
        :return: 
        """
        if not saveDir:
            saveDir=self.batchDir
        self.batchSettingsTree.write(saveDir + '/readTobiiGlassesSettings-'+os.path.splitext(os.path.basename(self.batchFile))[0]+'.xml')

    def md5(self,fname:str)->str:
        """Calculates and returns MD5 hash checksum of a file.

        From https://stackoverflow.com/a/3431838/2795533

        :param fname: file path.
        :return: md5 hex value.
        """
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()








    #getters and setters
    # def get_wd(self) -> str:
    #     """Returns data directory containing this settings file.
    #
    #     :return: file path str.
    #     """
    #     return self.wd
    #
    # def set_status_callback(self, status_callback: function) -> None:
    #     """
    #
    #     :param status_callback:
    #     :return:
    #     """
    #     self.status_callback = status_callback