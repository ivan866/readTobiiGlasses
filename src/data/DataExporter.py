import os
from datetime import datetime
import xml.etree.ElementTree as ET


import numpy

from pympi.Elan import Eaf

from scipy.interpolate import UnivariateSpline

from data.TobiiMEMS import TobiiMEMS
from data.IVTFilter import IVTFilter
import skinematics

import angles

import sqlite3

from SettingsReader import SettingsReader



class DataExporter():

    """Helper class that writes to files some particularly data channels useful for further data analysis."""

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()



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
            for file in self.settingsReader.getTypes('gaze'):
                if multiData.hasColumn('Eye movement type',file.get('id')):
                    written = True
                    fixFile = os.path.splitext(file.get('path'))[0] + '_fixations.' + format
                    sacFile = os.path.splitext(file.get('path'))[0] + '_saccades.' + format
                    #dropping human-unperceptable columns
                    #FIXME the function knows the column names, this is code smell!
                    if format == 'csv':
                        multiData.getChannelAndTag('fixations',file.get('id')).drop(columns=['Timedelta','Record tag','Id']).to_csv(self.settingsReader.dataDir + '/' + fixFile, sep='\t', index=False)
                        multiData.getChannelAndTag('saccades',file.get('id')).drop(columns=['Timedelta','Record tag','Id']).to_csv(self.settingsReader.dataDir + '/' + sacFile, sep='\t', index=False)
                    elif format == 'xls':
                        multiData.getChannelAndTag('fixations', file.get('id')).drop(columns=['Timedelta','Record tag','Id']).to_excel(self.settingsReader.dataDir + '/' + fixFile, index=False)
                        multiData.getChannelAndTag('saccades', file.get('id')).drop(columns=['Timedelta','Record tag','Id']).to_excel(self.settingsReader.dataDir + '/' + sacFile, index=False)
            if written:
                self.topWindow.setStatus('Fixations and saccades saved to files. Intervals tagged.')
            else:
                self.topWindow.setStatus('There is no data to write.')




    def exportGyro(self,multiData) -> None:
        """Writes gyroscope and accelerometer data to files. Generates .eaf tiers."""
        self.topWindow.logger.debug('export gyro')
        if self.settingsReader.check() and multiData.check():
            written = 0
            for file in self.settingsReader.getTypes('gaze'):
                channel='gyro'
                if multiData.hasChannelById(channel,file.get('id')):
                    written = written + 1
                    # #пишем файлы по отдельности
                    gyroFile = os.path.splitext(file.get('path'))[0] + '_gyro.csv'
                    #accelFile = os.path.splitext(file.get('path'))[0] + '_accelerometer.csv'
                    self.topWindow.setStatus('Writing gyro data (file {0})...'.format(os.path.basename(gyroFile)))
                    gyro=multiData.getChannelAndTag(channel, file.get('id'))
                    #accel=multiData.getChannelById('accel', file.get('id'))
                    #сохраняется интерполированный gyro
                    #gyro.drop(columns=['Timedelta','Record tag','Id']).to_csv(self.settingsReader.dataDir + '/' + gyroFile, sep='\t', index=False)
                    #self.topWindow.setStatus('Writing accelerometer data (file ' + os.path.basename(accelFile) + ')...')
                    #accel.drop(columns=['Timedelta','Record tag','Id']).to_csv(self.settingsReader.dataDir + '/' + accelFile, sep='\t', index=False)

                    #analytic gyroscope coordinates and angle
                    #gravity g=9.81 is filtered out based on assumption that initial orientation is numpy.eye(3)
                    #self.topWindow.setStatus('Solving 6-channel sensor stream analytically...')

                    # меняем оси местами чтобы компенсировать гравитацию именно по Y
                    #FIXME лишняя переменная, хранящая в себе копию данных
                    angularVelocity=gyro[['Gyro X', 'Gyro Y', 'Gyro Z']]#.as_matrix()
                    #acceleration=gyro[['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]#.as_matrix()

                    #FIXME tobii glasses accel frequency hard-coded (100 Hz, 10 ms/frame)
                    #sensor = TobiiMEMS(in_data={'rate': 100, 'acc': acceleration, 'omega': angularVelocity})
                    #sensor.calc_position()

                    #pos=numpy.diff(sensor.pos,axis=0)
                    #angles=skinematics.quat.quat2deg(sensor.quat)

                    #skinematics.view.orientation(sensor.quat[50000:50050], 'gyro01.mp4', 'Head orientation', 100)


                    #находим результирующую между тремя ортогональными углами
                    self.topWindow.setStatus('Compositing angles...')
                    angularVelocityScalar=[]
                    for pitch,roll,yaw in angularVelocity.as_matrix():
                        angleXY=angles.sep(0,angles.d2r(pitch),angles.d2r(roll),0)
                        angleXYZ=angles.sep(0,angleXY,angles.d2r(yaw),0)
                        angularVelocityScalar.append(angles.r2d(angleXYZ))
                    gyro.insert(4,'angVelScalar',angularVelocityScalar)

                    #сглаживаем
                    # spline=UnivariateSpline(x=numpy.linspace(0,100,num=len(angularVelocityScalar)),
                    #                                       y=angularVelocityScalar)
                    # xs=angularVelocityScalar
                    # ys=spline(xs)



                    #detecting head motion
                    self.topWindow.setStatus('Head motion detection...')
                    filter=IVTFilter()
                    #настройки фильтра
                    filter.setParameter('threshold',20.0)       #минимальная скорость движения (саккады), deg/s
                    filter.setParameter('dur_threshold',0.2)  #минимальная длительность отсутствия движения (фиксации), s
                    filter.process(data=gyro[['TimestampZeroBased','angVelScalar']])
                    #выбираем только моменты где есть движение
                    state='motions'
                    result=filter.groupStateTimes(state)
                    self.topWindow.setStatus('I-VT filter finished, with parameters: '+filter.printParams()+'. '+str(result.shape[0])+' '+state+' found.')


                    #generate .eaf
                    if True:#multiData.hasChannelById('ceph', file.get('id')):
                        cephFile=self.settingsReader.getPathAttrById('ceph',file.get('id'),absolute=True)
                        ceph=Eaf(cephFile)
                        #TODO проверить есть ли там уже такой слой
                        tier=channel+'_ceph_'+state
                        ceph.add_tier(tier_id=tier,ling='Default',
                                      part=file.get('id'),ann=self.topWindow.PROJECT_NAME)
                        for index,row in result.iterrows():
                            ceph.add_annotation(id_tier=tier,
                                                start=int(row['min']*1000),end=int(row['max']*1000),
                                                value=file.get('id')+'-'+str(int(round(row['mean'])))+' deg/s')
                        ceph.to_file(cephFile+'.rtg.eaf')

                    else:
                        self.topWindow.setStatus('Cephalic annotation not specified! No file to add tier to.')





            if written == 1:
                self.topWindow.setStatus('Available sensor data saved to files. Sparse gyro data filled with duplicates! Note that samples before zeroTime were removed and intervals tagged.')
            else:
                self.topWindow.setStatus('There is no sensor data to write.')


    def exportSQL(self,multiData:object)->None:
        """Writes all data to SQl database using SQLite.

        :param multiData: multiData object to write
        :return:
        """
        #TODO pivotData export to SQL
        if self.settingsReader.check() and multiData.check():
            self.topWindow.setStatus('Creating SQL database...')
            saveDir = self.createDir(prefix='export')
            dbFile=saveDir+'/sqlite.db'
            conn=sqlite3.connect(dbFile)
            multiData.getChannelById('ocul','N').to_sql('ocul',conn)

            self.topWindow.setStatus('Database ready. Intervals trimmed and tagged.')
            self.copyMeta()
        else:
            self.topWindow.setStatus('WARNING: No data loaded yet. Read data first!')