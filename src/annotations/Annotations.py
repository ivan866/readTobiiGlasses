import os
import re
import math
import subprocess

import numpy as np

import scipy as sp
from scipy.integrate import cumtrapz
from scipy.signal import savgol_filter

import pandas as pd
from pandas import DataFrame


from data.TobiiMEMS import TobiiMEMS
from data.IVTFilter import IVTFilter

import skinematics
import angles

import pympi
from pympi.Elan import Eaf


from SettingsReader import SettingsReader





#TODO ? can refactor eaf objects to dedicated annotation class through inheritance
#with methods for data manipulation and retrieval, including saving and formatting



#TODO ?- launch ExportTabdelimeted.java from elan*.jar and export to .txt, then read
def parseAnnotationToDataframe(topWindow, annotData:object, settingsReader:SettingsReader)-> DataFrame:
    """Parses all the tiers and makes a single dataframe from them.

    :param eafData: pympi.Elan object
    :return: dataframe with columns corresponding to tiers
    """
    if type(annotData) == pympi.Elan.Eaf:
        tierNames=annotData.get_tier_names()
    elif type(annotData) == pympi.Praat.TextGrid:
        tierNames=[t.name for t in annotData.get_tiers()]

    result=DataFrame(columns=['Begin_Time'])
    ids = settingsReader.unique(field='id')
    re_start='^[{0}][-|_]'.format('|'.join(ids))
    re_end='[-|_][{0}]$'.format('|'.join(ids))
    for tierName in tierNames:
        if type(annotData) == pympi.Elan.Eaf:
            annot=annotData.get_annotation_data_for_tier(tierName)
        elif type(annotData) == pympi.Praat.TextGrid:
            annot=annotData.get_tier(tierName).intervals
        else:
            topWindow.setStatus('ERROR: Unrecognized annotation type.')
            annot=None

        #удаляем из названия слоя букву-указатель на id коммуниканта (N,R,C,L,etc.), чтобы в сводных таблицах все соответственные названия были идентичны
        #она бывает в начале и в конце, отделена _ или -
        tierName=re.sub(re_start, '', tierName, flags=re.IGNORECASE)
        tierName=re.sub(re_end, '', tierName, flags=re.IGNORECASE)

        #при наличии родительского слоя возвращается более 3 столбцов
        tierDf=DataFrame(data=annot)
        tierDf=tierDf.iloc[:,0:3]
        tierDf.rename(columns={0:'Begin_Time',1:'Duration',2:tierName},inplace=True)
        #вырезаем табы, оставленные при конвертации из .xls с помощью yey.exe
        tierDf = tierDf.applymap(lambda x: re.sub('\t(.*)', '\\1', str(x)))
        #бывают пустые слои
        if len(tierDf):
            tierDf = tierDf.astype({'Begin_Time':float, 'Duration':float},copy=False)
            tierDf['Duration']=tierDf['Duration']-tierDf['Begin_Time']
            if type(annotData) == pympi.Elan.Eaf:
                tierDf['Begin_Time'] /= 1000
                tierDf['Duration'] /= 1000

            result=result.merge(tierDf, how='outer', sort=True, copy=False)

    #не совсем корректно удалять nan, но для удобства поиска допустимо, пока все столбцы консистентны
    #но тогда пустые будут влиять на подсчет средних (!) в статистике
    #FIXME скорее есть смысл заменять пустые ячейки на NaN
    #result.replace(to_replace=np.nan,value='',inplace=True)
    return result






# TODO в wiki вставить графики скорости и описать как происходит детекция и расширение границ
#FIXME можно вынести код детекции в отдельный класс gyro
def imuToEaf(topWindow, multiData, settingsReader:object,dataExporter:object) -> None:
    """Detects cephalic motion, generates tiers and exports to .eaf files, containing ceph annotations.

    :param topWindow:
    :param multiData:
    :param dataExporter:
    :return:
    """
    written=False
    localG = -9.81523
    for (channel, id) in multiData.genChannelIds(channel='imu'):
        if multiData.hasChannelById('ceph', id):
            topWindow.setStatus('Working with gyroscope data...')
            #исходный вариант - для угловой скорости, интерполированный - для сенсора
            imu = multiData.getChannelAndTag(channel, id)
            gyro = multiData.getChannelAndTag('gyro', id)
            #вычитаем mean offset IMU error
            #TODO снабдить это графиками - должен быть шум вокруг нуля по всем осям, график можно сразу сохранять либо выводить на экран
            means=multiData.getMeansByInterval(channel,id,interval='_static')
            if means is not None:
                imu['Gyro X']=imu['Gyro X']-means['Gyro X'][0]
                imu['Gyro Y']=imu['Gyro Y']-means['Gyro Y'][0]
                imu['Gyro Z']=imu['Gyro Z']-means['Gyro Z'][0]
                gyro['Gyro X']=gyro['Gyro X']-means['Gyro X'][0]
                gyro['Gyro Y']=gyro['Gyro Y']-means['Gyro Y'][0]
                gyro['Gyro Z']=gyro['Gyro Z']-means['Gyro Z'][0]

                imu['Accelerometer X']=imu['Accelerometer X']-means['Accelerometer X'][0]
                #очки лежа могут быть перевернуты
                #FIXME если запись вся перевернута, или очки лежали под углом к горизонту, то будет неправильно
                imu['Accelerometer Y']=imu['Accelerometer Y']+(abs(means['Accelerometer Y'][0])-abs(localG))
                imu['Accelerometer Z']=imu['Accelerometer Z']-means['Accelerometer Z'][0]

            # меняем оси местами чтобы компенсировать гравитацию именно по Y
            # FIXME лишняя переменная, хранящая в себе копию данных
            angVel = imu[['Gyro X', 'Gyro Z', 'Gyro Y']].as_matrix()
            acc = imu[['Accelerometer X', 'Accelerometer Z', 'Accelerometer Y']].as_matrix()
            # FIXME accel frequency hard-coded (100 Hz)
            #TODO вводить точное значение g в функцию analytical пакета skinematics - pull request
            #topWindow.setStatus('Integrating sensor data...')
            #FIXME указан множитель параметра omega для приведения данных к визуально правдоподобным значениям
            #TODO проверить графики скорости с offset (как можно дальше фильтровать скорость?, - она уже почти нормальная, только дрейфует) и без него, с приведением к радианам и без него
            #sensor = TobiiMEMS(in_data={'rate': topWindow.VIDEO_FRAMERATE, 'acc': acc, 'omega': angVel / 180 * sp.constants.pi})

            #в пакете она почему-то считается накопительной с помощью функции cumtrapz
            # positionM=np.vstack(([0, 0, 0], np.diff(sensor.pos,axis=0)))
            #velocityMS=np.vstack(([0, 0, 0], np.diff(sensor.vel,axis=0)))
            # rotationD=skinematics.quat.quat2deg(sensor.quat)

            # находим результирующую между тремя ортогональными углами
            #TODO попробовать детекцию без результирующих
            topWindow.setStatus('Finding result rotation...')
            angVel = gyro[['Gyro X', 'Gyro Z', 'Gyro Y']].as_matrix()
            angVelScalar = []
            for pitch, roll, yaw in angVel:
                angleXY = angles.sep(0, angles.d2r(pitch), angles.d2r(roll), 0)
                angleXYZ = angles.sep(0, angleXY, angles.d2r(yaw), 0)
                angVelScalar.append(angles.r2d(angleXYZ))
            angVelScalar = savgol_filter(angVelScalar, 5, 2)
            gyro.insert(4, 'angVelScalar', angVelScalar)

            # результирующий вектор скорости
            # TODO добавить график скорости головы в меню, и просмотреть его
            # TODO статистика амплитуд, скоростей и длительностей всех движений головы (main sequence)
            topWindow.setStatus('Finding jolt...')
            #topWindow.setStatus('Finding result velocity...')
            vel = np.vstack(([0, 0, 0], np.diff(acc, axis=0)))
            #vel = np.vstack(([0, 0, 0], np.diff(np.vstack(([0, 0, 0],cumtrapz(y=acc, x=imu['TimestampZeroBased'], axis=0))),axis=0)))
            velScalar = []
            for x, z, y in vel:
                velXY = math.hypot(x, y)
                velXYZ = math.hypot(velXY, z)
                velScalar.append(velXYZ)
            velScalar = savgol_filter(velScalar, 5, 2)
            imu.insert(4, 'velScalar', velScalar)


            # detecting head motion
            #TODO можно refactor в отдельные функции
            state = 'motions'
            topWindow.setStatus('Filtering ceph motion...')
            topWindow.setStatus('Rotation component...')
            filter = IVTFilter()
            #TODO как вариант подбирать пороги на основании шума в каждой конкретной записи или даже интервале
            filter.setParameter('min_velocity', 10.0)  # минимальная скорость движения
            filter.setParameter('noise_level', 3.0)  # максимальная скорость на границах движения
            filter.setParameter('min_static', 0.4)  # минимальная длительность отсутствия движения, s
            filter.setParameter('min_motion', 0.150)  # минимальная длительность движения, s
            filter.process(data=gyro[['TimestampZeroBased', 'angVelScalar']])
            result = filter.getResultFiltered(state)
            topWindow.setStatus('I-VT filter finished, with parameters: ' + filter.printParams() + '. ' + str(result.shape[0]) + ' ' + state + ' found.')

            topWindow.setStatus('Jolt component...')
            filter2 = IVTFilter()
            filter2.setParameter('min_velocity', 0.3)
            filter2.setParameter('noise_level', 0.12)
            filter2.setParameter('min_static', 0.4)
            filter2.setParameter('min_motion', 0.150)
            filter2.process(data=imu[['TimestampZeroBased', 'velScalar']])
            result2 = filter2.getResultFiltered(state)
            topWindow.setStatus('I-VT filter finished, with parameters: ' + filter2.printParams() + '. ' + str(result2.shape[0]) + ' ' + state + ' found.')

            # generate .eaf
            #TODO можно сделать refactor в универсальный метод writeEaf
            if not written:
                saveDir = dataExporter.createDir(prefix='annot')
                written = True
            cephFile = settingsReader.getPathAttrById('ceph', id)
            ceph = multiData.getChannelById('ceph', id)
            tier = id + '-cGyro' + state.capitalize()
            tier2 = id + '-cJolt' + state.capitalize()
            #tier2 = id + '-cVelocity' + state.capitalize()
            ceph.add_tier(tier_id=tier, ling='Default', part=id, ann=topWindow.PROJECT_NAME)
            ceph.add_tier(tier_id=tier2, ling='Default', part=id,ann=topWindow.PROJECT_NAME)
            for index, row in result.iterrows():
                ceph.add_annotation(id_tier=tier, start=int(row['min'] * 1000), end=int(row['max'] * 1000),
                                    value=str(int(round(row['mean']))) + ' deg/s')
            for index, row in result2.iterrows():
                ceph.add_annotation(id_tier=tier2, start=int(row['min'] * 1000), end=int(row['max'] * 1000),
                                    value=str(round(row['mean'], 1)) + ' m/s^3')
            eafFile = saveDir + '/' + os.path.splitext(cephFile)[0] + '-gyro.eaf'
            topWindow.setStatus('Saving ELAN file ({0}).'.format(eafFile))
            ceph.to_file(eafFile)
        else:
            topWindow.setStatus('Cephalic annotation pair not specified! No ELAN file to add tier to.',color='error')

    if written:
        dataExporter.copyMeta()
    else:
        topWindow.setStatus('Nothing was saved. No gyroscope data!',color='error')



def callPyper(topWindow, multiData, settingsReader:object,dataExporter:object, args:list) -> None:
    """

    :param topWindow:
    :param multiData:
    :param settingsReader:
    :param dataExporter:
    :param args: list of constants for detection
    :return:
    """
    #performing a dry run to bypass Pyper's question about overwriting the dir
    topWindow.setStatus('WARNING: this operation can take several hours for each record processed, depending on your machine speed.')
    saveDir=dataExporter.createDir(prefix=args[4],dryRun=True)
    cmd=['g:/ProgramData/Anaconda3Win7/python.exe',
         'g:/projects/multidiscourse/scripts/motionTracking/Pyper/Pyper-python3/src/tracking_cli.py',
         settingsReader.getPathAttrById('vi','N',absolute=True),
         #check different -b values vs. quality
         '-b','00:00',
         '-f','00:00',
         '-t','99:00',
         '--threshold',str(args[0]),
         '--min-area',str(args[1]),
         '--max-area',str(args[2]),
         '--teleportation-threshold',str(args[3]),
         '--plot',
         '--save-graphics',
         '--prefix',os.path.basename(saveDir)]
    output = subprocess.run(cmd, shell=True)

    topWindow.setStatus('Motion detection cycle finished. Check .eaf file.',color='success')
    dataExporter.copyMeta()

    #TODO all files of type
    #try AviSynth downscaled source. check quality difference
    #pyper installation
    #console output
    #compare fast and no-fast in .eaf
    #assessment


def pyperToEaf(topWindow, multiData, settingsReader:object,dataExporter:object) -> None:
    """Reads and parses Pyper output csv file, then exports to .eaf containing manu annotations.

    :param topWindow:
    :param multiData:
    :param settingsReader:
    :param dataExporter:
    :return:
    """
    #TODO refactor 'written' mechanism (all occurences) to callbacks
    written=False
    for fileElem in settingsReader.genTypeFile('pyper'):
        id=fileElem.get('id')
        if multiData.hasChannelById('manu', id):
            filePath = settingsReader.getPathAttrById('pyper', id, absolute=True)
            fileExt = os.path.splitext(filePath)[1]
            topWindow.setStatus('Reading Pyper output (' + os.path.basename(filePath) + ')...')
            if fileExt.lower() == '.csv':
                pyperData = pd.read_csv(filePath, header=None, sep=',', decimal='.', encoding='utf-8',
                                        names=['frame','x','y'], dtype={'frame':int,'x':float,'y':float})

                topWindow.setStatus('Finding hands distance (per frame)...')
                dist = []
                diffed=np.vstack(([0, 0, 0], np.diff(pyperData,axis=0)))
                pyperData[['x','y']]=diffed[:,1:3]
                for index, row in pyperData.iterrows():
                    distXY = math.hypot(row['x'], row['y'])
                    dist.append(distXY)
                pyperData.insert(3, 'dist', dist)

                # detecting manu motion
                #FIXME сделать refactor этого блока, вынести их все в одну функцию
                state = 'motions'
                topWindow.setStatus('Filtering manu motion...')
                filter = IVTFilter()
                filter.setParameter('min_velocity', 0.5)    #в пикселях
                filter.setParameter('noise_level', 0.15)    #в пикселях
                filter.setParameter('min_static', 20)       #в кадрах
                filter.setParameter('min_motion', 5)        #в кадрах
                filter.process(data=pyperData[['frame', 'dist']])
                result = filter.getResultFiltered(state)
                topWindow.setStatus('I-VT filter finished, with parameters: ' + filter.printParams() + '. ' + str(
                    result.shape[0]) + ' ' + state + ' found.')

                # generate .eaf
                if not written:
                    saveDir = dataExporter.createDir(prefix='annot')
                    written = True

                manuFile = settingsReader.getPathAttrById('manu', id)
                manu = multiData.getChannelById('manu', id)
                tier = id + '-mPyper' + state.capitalize()
                manu.add_tier(tier_id=tier, ling='Default', part=id, ann=topWindow.PROJECT_NAME)
                for index, row in result.iterrows():
                    #FIXME взять framerate из самого видеофайла при помощи opencv или ffmpeg, например
                    manu.add_annotation(id_tier=tier, start=int(row['min'] / topWindow.VIDEO_FRAMERATE *1000), end=int(row['max'] / topWindow.VIDEO_FRAMERATE *1000),
                                        value=str(int(round(row['mean']))) + ' ppf')
                eafFile = saveDir + '/' + os.path.splitext(manuFile)[0] + '-pyper_converted.eaf'
                topWindow.setStatus('Saving ELAN file ({0}).'.format(eafFile))
                manu.to_file(eafFile)
            else:
                topWindow.setStatus('Unknown file format.')
        else:
            topWindow.setStatus('Manual annotation pair not specified! No ELAN file to add tier to.',color='error')

    if written:
        dataExporter.copyMeta()
    else:
        topWindow.setStatus('Nothing was saved. No manu data!',color='error')



#TODO парование интервалов из greenpeople и ручной аннотации, затем ! поиск кластеров там, где много мелких кусков в GP
#TODO type attribute must be case insensitive
def qualityAssessment(topWindow, multiData, settingsReader:object,dataExporter:object) -> None:
    """

    :param topWindow:
    :param multiData:
    :param settingsReader:
    :param dataExporter:
    :return:
    """
    pass

