import os
from datetime import datetime
import xml.etree.ElementTree as ET



import sqlalchemy

from SettingsReader import SettingsReader



#FIXME class not needed, just methods
class DataExporter():

    """Helper class that writes to files some particularly data channels useful for further data analysis."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()
        self.colsUnperceptable=['Timedelta','Record tag','Id']



    def createDir(self,prefix:str='output',serial:bool=False,savePath:str='')->str:
        """Creates timestamped directory to save data into.

        :param prefix: directory name prefix.
        :param serial:
        :param savePath:
        :return: Directory path str.
        """
        now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
        dateTag = ET.Element('date')
        dateTag.text = now
        #TODO change append to set
        self.settingsReader.settings.append(dateTag)

        if serial:
            self.saveDir = savePath
        else:
            self.saveDir = self.settingsReader.dataDir + '/'+prefix+'_' + now
        os.makedirs(self.saveDir)
        return self.saveDir

    def copyMeta(self,saveDir:str='')->None:
        """Writes settings and report to previously created save directory.

        :param saveDir:
        :return:
        """
        if saveDir:
            metaDir=saveDir
        else:
            metaDir=self.saveDir
        self.settingsReader.save(metaDir)
        self.topWindow.setStatus('Settings included for reproducibility.')
        self.topWindow.saveReport(metaDir)




    def exportFixations(self,multiData,format:str) -> None:
        """Writes fixations and saccades to files.
        
        :param format: 'xls' or 'csv'.
        :return: None.
        """
		#TODO merge speaking and listening mode for each participant with fixation status (Kendon stats)
        self.topWindow.logger.debug('export fixations')
        if self.settingsReader.check() and multiData.check():
            written = False
            #TODO change to iterator pattern using generators
            for file in self.settingsReader.getTypes('gaze'):
                id=file.get('id')
                if multiData.hasColumn('Eye movement type',id):
                    if not written:
                        saveDir = self.createDir(prefix='export')
                    written = True
                    fixFile = os.path.splitext(file.get('path'))[0] + '_fixations.' + format
                    sacFile = os.path.splitext(file.get('path'))[0] + '_saccades.' + format
                    #dropping human-unperceptable columns
                    #FIXME the function knows the column names, this is code smell!
                    if format == 'csv':
                        multiData.getChannelAndTag('fixations',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + fixFile, sep='\t', index=False)
                        multiData.getChannelAndTag('saccades',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + sacFile, sep='\t', index=False)
                    elif format == 'xls':
                        multiData.getChannelAndTag('fixations', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + fixFile, index=False)
                        multiData.getChannelAndTag('saccades', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + sacFile, index=False)
            if written:
                self.topWindow.setStatus('Fixations and saccades saved to files. Intervals tagged.')
                self.copyMeta()
            else:
                self.topWindow.setStatus('There is no data to write.')




    def exportGyro(self,multiData) -> None:
        """Writes gyroscope and accelerometer data to files. Generates .eaf tiers."""

        self.topWindow.logger.debug('export gyro')
        if self.settingsReader.check() and multiData.check():
            written = 0
            #TODO change to iterator pattern
            for file in self.settingsReader.getTypes('gaze'):
                channel='gyro'
                if multiData.hasChannelById(channel,file.get('id')):
                    if not written:
                        saveDir = self.createDir(prefix='export')
                    written = written + 1
                    #пишем файлы по отдельности
                    gyroFile = os.path.splitext(file.get('path'))[0] + '_gyro.csv'
                    accelFile = os.path.splitext(file.get('path'))[0] + '_accelerometer.csv'
                    self.topWindow.setStatus('Writing gyro data (file {0})...'.format(os.path.basename(gyroFile)))
                    gyro=multiData.getChannelAndTag(channel, file.get('id'))
                    accel=multiData.getChannelAndTag('accel', file.get('id'))
                    gyro.drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + gyroFile, sep='\t', index=False)
                    self.topWindow.setStatus('Writing accelerometer data (file ' + os.path.basename(accelFile) + ')...')
                    accel.drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + accelFile, sep='\t', index=False)

            if written > 0:
                self.topWindow.setStatus('Available sensor data saved to files. Note that samples before zeroTime were removed and intervals tagged.')
                self.copyMeta()
            else:
                self.topWindow.setStatus('There is no sensor data to write.')





    #TODO SQL export issue + praat annotations
    def exportSQL(self,multiData:object)->None:
        """Writes all data to SQl database using SQLite.

        :param multiData: multiData object to write
        :return:
        """
        #TODO pivotData export to SQL
        # if self.settingsReader.check() and multiData.check():
        #     self.topWindow.setStatus('Creating SQL database...')
        #     saveDir = self.createDir(prefix='export')
        #     dbFile=saveDir+'/sqlite.db'
        #     conn=sqlite3.connect(dbFile)
        #     multiData.getChannelById('ocul','N').to_sql('ocul',conn)
        #
        #     self.topWindow.setStatus('Database ready. Intervals trimmed and tagged.')
        #     self.copyMeta()
        # else:
        #     self.topWindow.setStatus('WARNING: No data loaded yet. Read data first!')
        pass