import os
import re
import hashlib


import pandas as pd


from pympi.Elan import Eaf




class DataReader():

    """Helper class that reads and parses Tobii eyetracking data and all types of multidiscourse annotations."""

    def __init__(self,topWindow):
        self.topWindow = topWindow



    def determineSkiprows(self,file:str,commentStr:str)->int:
        """
        
        :param file: 
        :param commentStr: 
        :return: 
        """
        with open(file,encoding='UTF-8') as f:
            lineNum = 0
            line = f.readline()
            while line.startswith(commentStr):
                lineNum = lineNum + 1
                line = f.readline()
            return lineNum


    def read(self, settingsReader, multiData,serial:bool=False) -> None:
        """Actual data parsing code.
        
        Depends on pandas module.

        :param settingsReader: SettingsReader object to get xml settings tree from.
        :param multiData: MultiData object to write into.
        :param serial: If this is a serial batch.
        :return: 
        """
        self.topWindow.logger.debug('reading data...')
        if settingsReader.check():
            settingsReader.read(serial=serial)
        else:
            return

        multiData.reset()
        self.readTobii(settingsReader, multiData, serial=serial)
        self.readManu(settingsReader, multiData, serial=serial)
        self.readCeph(settingsReader, multiData, serial=serial)
        self.readOcul(settingsReader, multiData, serial=serial)
        self.topWindow.setStatus('All valuable data read successfully.')



    def readTobii(self,settingsReader, multiData,serial:bool=False)->None:
        """Reads Tobii Glasses 2 gaze data from .tsv file.
        
        :param settingsReader: 
        :param multiData: 
        :param serial: 
        :return: 
        """
        settingsGaze = settingsReader.getTypes('gaze')
        if len(settingsGaze):
            self.topWindow.setStatus('Reading gaze data...')
            for file in settingsGaze:
                gazeFile = settingsReader.dataDir + '/' + file.get('path')
                if os.path.exists(gazeFile):
                    self.topWindow.setStatus('Reading gaze data (file ' + os.path.basename(gazeFile) + ')...')
                    # узнаем какие столбцы присутствуют
                    headers = pd.read_table(gazeFile, nrows=1, encoding='UTF-16')
                    availColumns = [i for i in list(headers.columns) if re.match('Recording timestamp|Gaze point|Gaze 3D position|Gaze direction|Pupil diameter|Eye movement type|Gaze event duration|Fixation point|Gyro|Accelerometer',i)]
                    multiData.setNode('availColumns',file.get('id'),availColumns)
                    gazeData = pd.read_table(gazeFile, decimal=",", encoding='UTF-16',
                                                 # ==============================================================================
                                                 # numpy не поддерживает столбцы типа integer в которых есть NA
                                                 #                          dtype={'Recording timestamp':numpy.float32,
                                                 #                                 'Gaze point X':numpy.float16, 'Gaze point Y':numpy.float16,
                                                 #                                 'Pupil diameter left':numpy.float32, 'Pupil diameter right':numpy.float32,
                                                 #                                 'Eye movement type':numpy.str, 'Gaze event duration':numpy.float16, 'Eye movement type index':numpy.float16,
                                                 #                                 'Fixation point X':numpy.float16, 'Fixation point Y':numpy.float16},
                                                 # ==============================================================================
                                                 usecols=availColumns)
                    # переводим в секунды
                    gazeData['Recording timestamp'] /= 1000
                    gazeData['Gaze event duration'] /= 1000
                    # оставляем достаточную точность
                    # gazeData=gazeData.round(6)



                    self.topWindow.logger.debug('gaze data read successfully')
                    # гироскоп (95 Гц) и акселерометр (100 Гц) пишутся не синфазно с трекером, приходится заполнять пустоты в gyro
                    if multiData.hasAllColumns(['Gyro X','Gyro Y','Gyro Z','Accelerometer X','Accelerometer Y','Accelerometer Z'],file.get('id')):
                        #imu
                        #FIXME копируются столбцы с данными
                        gyro = gazeData[['Recording timestamp',
                                         'Gyro X', 'Gyro Y', 'Gyro Z']]
                        accel = gazeData[['Recording timestamp',
                                          'Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]
                        gyro.set_index (keys='Recording timestamp',drop=False,inplace=True)
                        accel.set_index(keys='Recording timestamp',drop=False,inplace=True)
                        # заполняем недостающие строки по гироскопу
                        gyro.interpolate(method='index',inplace=True)
                        gyro=pd.concat(objs=(gyro, accel[['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]),axis=1)
                        # убираем пустые строки, но без учета столбца времени
                        gyro.dropna(subset=(['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']), how='all', inplace=True)
                        # если остались еще пустые ячейки в начале записи
                        gyro.fillna(value=0,inplace=True)
                        multiData.setNode('imu',file.get('id'),gyro)

                        #FIXME doubled data
                        #gyro/accel
                        gyro = gazeData[['Recording timestamp','Gyro X', 'Gyro Y', 'Gyro Z']]
                        accel = gazeData[['Recording timestamp','Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]
                        # убираем пустые строки, но без учета столбца времени
                        gyro.dropna(subset=(['Gyro X', 'Gyro Y', 'Gyro Z']), how='all', inplace=True)
                        accel.dropna(subset=(['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']), how='all', inplace=True)
                        multiData.setNode('gyro', file.get('id'), gyro)
                        multiData.setNode('accel',file.get('id'), accel)

                        # гироскоп в основных данных больше не нужен
                        gazeData.drop(['Gyro X', 'Gyro Y', 'Gyro Z', 'Accelerometer X', 'Accelerometer Y', 'Accelerometer Z'], axis=1, inplace=True)
                    else:
                        self.topWindow.setStatus('No gyroscope/accelerometer data in file {0}!'.format(os.path.basename(gazeFile)))



                    # убираем пустые строки
                    gazeData = gazeData[(gazeData['Gaze point X'].notnull()) & (gazeData['Gaze point Y'].notnull()) | \
                                        (gazeData['Eye movement type'] == 'EyesNotFound')]


                    if multiData.hasColumn('Eye movement type',file.get('id')):
                        # вырезаем строки с фиксациями
                        fixations = gazeData.loc[gazeData['Eye movement type'] == 'Fixation'][['Recording timestamp',
                                                                                               'Gaze event duration',
                                                                                               'Eye movement type index',
                                                                                               'Fixation point X',
                                                                                               'Fixation point Y']]
                        # удаляем одинаковые строки, но без учета первого столбца
                        fixations.drop_duplicates(fixations.columns[range(1, fixations.shape[1])], inplace=True)
                        timeReadable = pd.to_datetime(fixations['Recording timestamp'], unit='s')
                        fixations.insert(1, 'Timecode', timeReadable.dt.strftime('%M:%S.%f'))
                        multiData.setNode('fixations',file.get('id'),fixations)

                        # теперь саккады
                        # при частоте 50 Гц координаты начала и конца саккад не достоверны
                        # def calcSaccadeGazePoints(row):
                        #     prevPosInd=numpy.where(gazeData['Recording timestamp']<row['Recording timestamp'])[0][-1]
                        #     prevX=gazeData.iloc[prevPosInd]['Gaze point X']
                        #     prevY=gazeData.iloc[prevPosInd]['Gaze point Y']
                        #     row['Start gaze point X']=prevX
                        #     row['Start gaze point Y']=prevY
                        #
                        #     nextPosInd=numpy.where(gazeData['Recording timestamp']>=((row['Recording timestamp']+row['Gaze event duration']).round(6)))[0][0]
                        #     nextX=gazeData.iloc[nextPosInd]['Gaze point X']
                        #     nextY=gazeData.iloc[nextPosInd]['Gaze point Y']
                        #     row['End gaze point X']=nextX
                        #     row['End gaze point Y']=nextY
                        #
                        #     return row

                        saccades = gazeData.loc[gazeData['Eye movement type'] == 'Saccade'][['Recording timestamp',
                                                                                             'Gaze event duration',
                                                                                             'Eye movement type index']]
                        saccades.drop_duplicates(saccades.columns[range(1, saccades.shape[1])], inplace=True)
                        # self.topWindow.setStatus('Parsing saccades (file '+os.path.basename(gazeFile)+')...')
                        # saccades=saccades.apply(calcSaccadeGazePoints,axis=1)
                        # saccades=saccades[['Recording timestamp',
                        #                    'Gaze event duration','Eye movement type index',
                        #                    'Start gaze point X','Start gaze point Y',
                        #                    'End gaze point X','End gaze point Y']]
                        timeReadable=pd.to_datetime(saccades['Recording timestamp'], unit='s')
                        saccades.insert(1,'Timecode',timeReadable.dt.strftime('%M:%S.%f'))
                        multiData.setNode('saccades',file.get('id'),saccades)


                        # участки потерянного контакта
                        eyesNotFounds = gazeData.loc[gazeData['Eye movement type'] == 'EyesNotFound'][['Recording timestamp',
                                                                                                       'Gaze event duration',
                                                                                                       'Eye movement type index']]
                        eyesNotFounds.drop_duplicates(eyesNotFounds.columns[range(1, eyesNotFounds.shape[1])], inplace=True)
                        multiData.setNode('eyesNotFounds',file.get('id'),eyesNotFounds)

                        # неизвестные события
                        unclassifieds = gazeData.loc[gazeData['Eye movement type'] == 'Unclassified'][['Recording timestamp',
                                                                                                       'Gaze point X',
                                                                                                       'Gaze point Y',
                                                                                                       'Gaze event duration',
                                                                                                       'Eye movement type index']]
                        unclassifieds.drop_duplicates(unclassifieds.columns[range(1, unclassifieds.shape[1])], inplace=True)
                        multiData.setNode('unclassifieds',file.get('id'),unclassifieds)


                        # события в основных данных больше не нужны
                        gazeData.drop(['Eye movement type', 'Gaze event duration', 'Eye movement type index',
                                       'Fixation point X', 'Fixation point Y'],
                                       axis=1, inplace=True)

                    multiData.setNode('gaze',file.get('id'),gazeData)
                    file.set('md5',self.md5(gazeFile))
                else:
                    self.topWindow.setStatus('Gaze file specified in settings (' + os.path.basename(gazeFile) + ') does not exist!')
        else:
            self.topWindow.setStatus('No gaze data specified in settings.')



    def readManu(self, settingsReader, multiData, serial: bool = False) -> None:
        """Reads manu annotation from txt file.

        :param settingsReader: 
        :param multiData: 
        :param serial: 
        :return: 
        """
        self.topWindow.logger.debug('reading manu data...')
        settingsManu = settingsReader.getTypes('manu')
        if len(settingsManu):
            self.topWindow.setStatus('Reading manu annotations...')
            for file in settingsManu:
                manuFile = settingsReader.dataDir + '/' + file.get('path')
                if os.path.exists(manuFile):
                    self.topWindow.setStatus('Reading manu annotation (file ' + os.path.basename(manuFile) + ')...')
                    skiprows=self.determineSkiprows(manuFile,'"#')
                    manuData = pd.read_table(manuFile, skiprows=skiprows)
                    #названия столбцов не всегда одинаковые в разных записях
                    manuData.rename(columns={col: re.sub('.*m.*gesture.*', 'mGesture', col, flags=re.IGNORECASE) for col in manuData.columns}, inplace=True)
                    #manuData.rename(columns={col: re.sub('.*lt.*phases.*','mLtPhases',col,flags=re.IGNORECASE) for col in manuData.columns},inplace=True)
                    #manuData.rename(columns={col: re.sub('.*rt.*phases.*', 'mRtPhases', col,flags=re.IGNORECASE) for col in manuData.columns},inplace=True)
                    multiData.setNode('manu',file.get('id'),manuData)
                    file.set('md5',self.md5(manuFile))
                else:
                    self.topWindow.setStatus('Manu file specified in settings (' + os.path.basename(manuFile) + ') does not exist!')
        else:
            self.topWindow.setStatus('No manu annotations specified in settings.')



    def readCeph(self, settingsReader, multiData, serial: bool = False) -> None:
        """Reads ceph annotation from ELAN .eaf file.

        :param settingsReader:
        :param multiData:
        :param serial:
        :return:
        """
        self.topWindow.logger.debug('reading ceph data...')
        settingsCeph = settingsReader.getTypes('ceph')
        if len(settingsCeph):
            self.topWindow.setStatus('Reading ceph annotations...')
            for file in settingsCeph:
                cephFile = settingsReader.dataDir + '/' + file.get('path')
                if os.path.exists(cephFile):
                    self.topWindow.setStatus('Reading ceph annotation (file ' + os.path.basename(cephFile) + ')...')
                    cephData = Eaf(cephFile)
                    multiData.setNode('ceph', file.get('id'), cephData)
                    file.set('md5', self.md5(cephFile))
                else:
                    self.topWindow.setStatus('Ceph file specified in settings (' + os.path.basename(cephFile) + ') does not exist!')
        else:
            self.topWindow.setStatus('No ceph annotations specified in settings.')


    def readOcul(self, settingsReader, multiData, serial: bool = False) -> None:
        """Reads ocul annotation from Excel file.

        :param settingsReader: 
        :param multiData: 
        :param serial: 
        :return: 
        """
        self.topWindow.logger.debug('reading ocul data...')
        settingsOcul = settingsReader.getTypes('ocul')
        if len(settingsOcul):
            self.topWindow.setStatus('Reading ocul annotations...')
            for file in settingsOcul:
                oculFile = settingsReader.dataDir + '/' + file.get('path')
                if os.path.exists(oculFile):
                    self.topWindow.setStatus('Reading ocul annotation (file ' + os.path.basename(oculFile) + ')...')
                    oculData = pd.read_excel(oculFile, header=None,
                                                 names=('Timecode',
                                                        'Gaze event duration',
                                                        'Id', 'Tier'),
                                                 usecols='B:E')
                    #при считывании из excel в строках могут оставаться знаки \t
                    oculData=oculData.applymap(lambda x: re.sub('\t(.*)', '\\1', str(x)))
                    oculData=oculData.astype({'Gaze event duration':int})
                    oculData['Gaze event duration'] /= 1000
                    multiData.setNode('ocul',file.get('id'),oculData)
                    file.set('md5',self.md5(oculFile))
                else:
                    self.topWindow.setStatus('Ocul file specified in settings (' + os.path.basename(oculFile) + ') does not exist!')
        else:
            self.topWindow.setStatus('No ocul annotations specified in settings.')



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