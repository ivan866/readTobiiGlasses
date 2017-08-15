import os

from SettingsReader import SettingsReader



class DataExporter():

    """Helper class that writes to files some particularly data channels useful for further data analysis."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()



    def exportFixations(self,multiData,format:str) -> None:
        """Writes fixations and saccades to files.
        
        :param format: 'xls' or 'csv'.
        :return: None.
        """
        if self.settingsReader.check() and multiData.check():
            written = False
            for file in self.settingsReader.getTypes('gaze'):
                if multiData.hasColumn('Eye movement type',file.get('id')):
                    written = True
                    fixFile = os.path.splitext(file.get('path'))[0] + '_Fixations.' + format
                    sacFile = os.path.splitext(file.get('path'))[0] + '_Saccades.' + format
                    if format == 'csv':
                        multiData.getChannelById('fixations',file.get('id')).to_csv(self.settingsReader.dataDir + '/' + fixFile, sep='\t', index=False)
                        multiData.getChannelById('saccades',file.get('id')).to_csv(self.settingsReader.dataDir + '/' + sacFile, sep='\t', index=False)
                    elif format == 'xls':
                        multiData.getChannelById('fixations', file.get('id')).to_excel(self.settingsReader.dataDir + '/' + fixFile, index=False)
                        multiData.getChannelById('saccades', file.get('id')).to_excel(self.settingsReader.dataDir + '/' + sacFile, index=False)
            if written:
                self.topWindow.setStatus('Fixations and saccades saved to files. Note that data before zeroTime is still present in exported data.')
            else:
                self.topWindow.setStatus('There is no data to write.')



    def exportGyro(self,multiData) -> None:
        """Writes gyroscope and accelerometer data to files."""
        if self.settingsReader.check() and multiData.check():
            written = 0
            for file in self.settingsReader.getTypes('gaze'):
                if multiData.hasChannelById('gyro',file.get('id')):
                    written = written + 1
                    gyroFile = os.path.splitext(file.get('path'))[0] + '_Gyro.csv'
                    self.topWindow.setStatus('Writing gyro data (file ' + os.path.basename(gyroFile) + ')...')
                    multiData.getChannelById('gyro', file.get('id')).to_csv(self.settingsReader.dataDir + '/' + gyroFile, sep='\t', index=False)
                if multiData.hasChannelById('accel',file.get('id')):
                    written = written + 10
                    accelFile = os.path.splitext(file.get('path'))[0] + '_Accelerometer.csv'
                    self.topWindow.setStatus('Writing accelerometer data (file ' + os.path.basename(accelFile) + ')...')
                    multiData.getChannelById('accel', file.get('id')).to_csv(self.settingsReader.dataDir + '/' + accelFile, sep='\t', index=False)
            if written == 1:
                self.topWindow.setStatus('Available gyroscope data saved to files. Note that data before zeroTime is still present in exported data.')
            elif written == 10:
                self.topWindow.setStatus('Available accelerometer data saved to files. Note that data before zeroTime is still present in exported data.')
            elif written == 11:
                self.topWindow.setStatus('Both available gyroscope and accelerometer data saved to files. Note that data before zeroTime is still present in exported data.')
            else:
                self.topWindow.setStatus('There is no sensor data to write.')