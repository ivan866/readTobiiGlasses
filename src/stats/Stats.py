import os
from datetime import datetime

from tkinter import *

import xml.etree.ElementTree as ET

from SettingsReader import SettingsReader



class Stats():

    """Statistical methods for multidiscourse data."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()



    def descriptive(self,multiData) -> None:
        """Basic data summary.
        
        Data description, length, number of channels, etc. Means, medians and distributions, grouped by channels and overall.
        
        :return: 
        """
        now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
        dateTag = ET.Element('date')
        dateTag.text = now
        self.settingsReader.settings.append(dateTag)

        saveDir = self.settingsReader.dataDir + '/stats_' + now
        os.mkdir(saveDir)


        data=multiData.getChannelById('ocul','N')
        tmpData=multiData.getDataInterval(data,'tell')
        # for channel in data['ocul']:
        #     for interval in settings.findall("interval"):
        #         dataChannel=data['ocul'][channel]
        #         dataChannel['Timecode']<datetime.strptime(interval.get('duration'),'%M:%S.%f').time()


        reportFile=open(saveDir + '/report.txt','w')
        reportFile.write(self.topWindow.report.get('0.0',END))
        reportFile.close()

        self.settingsReader.settingsTree.write(saveDir + '/' + os.path.basename(self.settingsReader.settingsFile))
        self.topWindow.setStatus('Statistics report saved. Settings included for reproducibility.')



    def save(self) -> None:
        """Writes calculated statistic to file."""
        pass