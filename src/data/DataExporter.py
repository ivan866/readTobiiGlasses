import os
from datetime import datetime
import xml.etree.ElementTree as ET



import pandas
from pandas import DataFrame
#import pandas.io.excel.xlsx.writer

import sqlalchemy

from SettingsReader import SettingsReader



#FIXME class not needed, just methods
class DataExporter():

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
            self.topWindow.setStatus('Settings included for reproducibility.')
            self.topWindow.saveReport(metaDir)




    #method may be superseded by exportCSV
    def exportFixations(self,multiData,format:str) -> None:
        """Writes fixations and saccades to files.
        
        :param format: 'xls' or 'csv'.
        :return: None.
        """
		#TODO merge speaking and listening mode for each participant with fixation status (Kendon stats)
        self.topWindow.logger.debug('export fixations')
        if self.settingsReader.check() and multiData.check():
            self.topWindow.setStatus('WARNING: This method is deprecated and not maintained. Use All tables to CSV/Excel instead.')
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
                    enfFile = os.path.splitext(file.get('path'))[0] + '_eyesNotFounds.' + format
                    uncFile = os.path.splitext(file.get('path'))[0] + '_unclassifieds.' + format
                    #dropping human-unperceptable columns
                    #FIXME the function knows the column names, this is code smell!
                    if format == 'csv':
                        multiData.getChannelAndTag('fixations',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + fixFile, sep='\t', index=False)
                        multiData.getChannelAndTag('saccades',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + sacFile, sep='\t', index=False)
                        multiData.getChannelAndTag('eyesNotFounds',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + enfFile, sep='\t', index=False)
                        multiData.getChannelAndTag('unclassifieds',id).drop(columns=self.colsUnperceptable).to_csv(saveDir + '/' + uncFile, sep='\t', index=False)
                    elif format == 'xls':
                        multiData.getChannelAndTag('fixations', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + fixFile, index=False)
                        multiData.getChannelAndTag('saccades', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + sacFile, index=False)
                        multiData.getChannelAndTag('eyesNotFounds', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + enfFile, index=False)
                        multiData.getChannelAndTag('unclassifieds', id).drop(columns=self.colsUnperceptable).to_excel(saveDir + '/' + uncFile, index=False)
            if written:
                self.topWindow.setStatus('Fixations and saccades saved to files. Intervals tagged.',color='success')
                self.copyMeta()
            else:
                self.topWindow.setStatus('There is no data to write.')




    # method may be superseded by exportCSV
    def exportGyro(self,multiData) -> None:
        """Writes gyroscope and accelerometer data to files. Generates .eaf tiers."""

        self.topWindow.logger.debug('export gyro')
        if self.settingsReader.check() and multiData.check():
            self.topWindow.setStatus('WARNING: This method is deprecated and not maintained. Use All tables to CSV instead.')
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
                self.topWindow.setStatus('Available sensor data saved to files. Note that samples before zeroTime were removed and intervals tagged.',color='success')
                self.copyMeta()
            else:
                self.topWindow.setStatus('There is no sensor data to write.')






    def exportCSV(self, multiData:object, format:str='csv')->None:
        """Writes all data to CSV files.

        Useful for further manual import into MySQL.

        :param multiData:
        :param format:
        :return:
        """
        if self.settingsReader.check() and multiData.check():
            self.topWindow.setStatus('Exporting data channels to {0}.'.format(format.upper()))
            saveDir = self.createDir(prefix='export')
            if format == 'xlsx':
                writer = pandas.ExcelWriter('{0}/channels_appended.{1}'.format(saveDir, format))

            for type in multiData.multiData.keys():
                #appended=False
                startrow = 0
                stacked=DataFrame()
                file = '{0}/{1}_appended.{2}'.format(saveDir, type, format)
                for (channel, id) in multiData.genChannelIds(channel=type):
                    data = multiData.getChannelAndTag(channel, id, 'dataframe', ignoreEmpty=True)
                    #if format=='csv':
                    #data.to_csv(file, sep='\t', header=not appended, index=False, mode='a')
                    stacked=stacked.append(data, sort=False)
                    #appended=True

                if format=="csv" and len(stacked):
                    stacked.to_csv(file, sep='\t', header=True, index=False, mode='w')
                elif format=='xlsx' and len(stacked):
                    stacked.to_excel(writer, header=True, index=False, sheet_name=channel, startrow=0, freeze_panes=(1,0), engine='pandas.io.excel.xlsx.writer')
                    #startrow = startrow + data.shape[0]

            if format=='xlsx':
                writer.save()

            self.topWindow.setStatus('Done. Intervals trimmed and tagged.', color='success')
            self.copyMeta()





    #TODO SQL export issue
    #TODO надо почитать как вообще комбинируются запросы в текстовое выражение, какие приемы существуют
    #TODO форму преобразования в таблицы см. в описании issue
    def exportSQL(self,multiData:object)->None:
        """Writes all data to SQl database using SQLite.

        :param multiData: multiData object to write
        :return:
        """
        if self.settingsReader.check() and multiData.check():
            self.topWindow.setStatus('Creating SQL database...')
            saveDir = self.createDir(prefix='export')
            dbFile=saveDir+'/db.sql'
            conn=sqlalchemy.connect(dbFile)
            multiData.getChannelAndTag('ocul','N').to_sql('ocul', conn, flavor='mysql')

            self.topWindow.setStatus('Database ready. Intervals trimmed and tagged.',color='success')
            self.copyMeta()
