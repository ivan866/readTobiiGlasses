import os
from datetime import datetime
import xml.etree.ElementTree as ET



from pandas import DataFrame

import sqlalchemy

from SettingsManager import SettingsManager



#FIXME class not needed, just methods
class OutputWriter():

    """Helper class that writes to files some particularly data channels useful for further data analysis."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()
        self.saveDir=''
        self.colsUnperceptable=['Timedelta','Record tag','Id']



    def createDir(self,prefix:str='output',serial:bool=False,savePath:str='',dryRun:bool=False)->str:
        """Creates timestamped directory to save data into.

        :param prefix: directory name prefix.
        :param serial:
        :param savePath:
        :param dryRun: whether to actually create the dir or just generate the path
        :return: Directory path str.
        """
        if self.settingsReader.check(full=True):
            now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
            dateTag = ET.Element('date')
            dateTag.text = now
            #TODO change append to set
            #при повторном использованиии файла настроек тегов с датой будет несколько
            self.settingsReader.settings.append(dateTag)

            if serial:
                self.saveDir = savePath
            else:
                self.saveDir = self.settingsReader.dataDir + '/'+str(prefix)+'_' + now

            if not dryRun:
                os.makedirs(self.saveDir)
            return self.saveDir
        else:
            raise ValueError('No settings found')


    def copyMeta(self,saveDir:str='')->None:
        """Writes settings and report to previously created save directory.

        :param saveDir:
        :return:
        """
        if self.settingsReader.check():
            if saveDir:
                metaDir=saveDir
            else:
                metaDir=self.saveDir
            self.settingsReader.save(metaDir)
            self.topWindow.set_status('Settings included for reproducibility.')
            self.topWindow.save_report(metaDir)




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
                self.topWindow.set_status('Fixations and saccades saved to files. Intervals tagged.', color='success')
                self.copyMeta()
            else:
                self.topWindow.set_status('There is no data to write.')




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
                    self.topWindow.set_status('Writing gyro data (file {0})...'.format(os.path.basename(gyroFile)))
                    gyro=multiData.getChannelAndTag(channel, file.get('id'))
                    accel=multiData.getChannelAndTag('accel', file.get('id'))
                    gyro.drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + gyroFile, sep='\t', index=False)
                    self.topWindow.set_status('Writing accelerometer data (file ' + os.path.basename(accelFile) + ')...')
                    accel.drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + accelFile, sep='\t', index=False)

            if written > 0:
                self.topWindow.set_status('Available sensor data saved to files. Note that samples before zeroTime were removed and intervals tagged.', color='success')
                self.copyMeta()
            else:
                self.topWindow.set_status('There is no sensor data to write.')






    def exportCSV(self, multiData:object)->None:
        """Writes all data to CSV files.

        Useful for further manual import into MySQL.

        :param multiData:
        :return:
        """
        pass





    #TODO учитывать stereotype constraints, не дублировать данные границ интервалов в sql-таблицах!
    #TODO SQL export issue + praat annotations
    #TODO надо почитать как вообще комбинируются запросы в текстовое выражение, какие приемы существуют
    #TODO форму преобразования в таблицы см. в описании issue
    #TODO сначала проверить что txt и eaf считались идентично
    def exportSQL(self,multiData:object)->None:
        """Writes all data to SQl database using SQLite.

        :param multiData: multiData object to write
        :return:
        """
        #TODO pivotData export to SQL
        if self.settingsReader.check() and multiData.check():
            self.topWindow.set_status('Creating SQL database...')
            saveDir = self.createDir(prefix='export')
            dbFile=saveDir+'/db.sql'
            conn=sqlalchemy.connect(dbFile)
            multiData.getChannelAndTag('ocul','N').to_sql('ocul', conn, flavor='mysql')

            self.topWindow.set_status('Database ready. Intervals trimmed and tagged.', color='success')
            self.copyMeta()
