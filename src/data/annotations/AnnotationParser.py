import os
import re


import pandas as pd


from pympi.Elan import Eaf
from pympi.Praat import TextGrid
import praatio
from praatio import tgio

from annotations import Annotations






class AnnotationParser():

    """Helper class that reads and parses Tobii eyetracking data and all types of multidiscourse annotations."""

    def __init__(self, topWindow):
        self.topWindow = topWindow







    #multiDatas are not combined in batch mode, instead, they are processed sequentially - for memory efficiency, and then only (csv) tables are pivoted
    def read(self, settings_manager:object, annotation_data:object, serial:bool=False) -> None:
        """Actual data parsing code.
        
        Depends on pandas module.

        :param settings_manager: SettingsReader object to get xml settings tree from.
        :param annotation_data: MultiData object to write into.
        :param serial: If this is a serial batch.
        :return: 
        """
        self.topWindow.logger.debug('reading data...')
        if settings_manager.check():
            settings_manager.read(serial=serial)
        else:
            return


        annotation_data.reset()
        try:
            self.read_tobii(settings_manager, annotation_data)
            self.read_voc(settings_manager, annotation_data)
            self.readManu(settings_manager, annotation_data)
            self.readCeph(settings_manager, annotation_data)
            self.readOcul(settings_manager, annotation_data)
            if settings_manager.check(full=True) and annotation_data.check():
                self.status_callback('All valuable data read successfully.', color='success')
        except:
            self.topWindow.report_error()
            raise






    #TODO format-aware parser (tsv, json)
    def read_tobii(self, settingsReader, multiData)->None:
        """Reads Tobii Glasses 2 gaze data from .tsv or json file.
        
        :param settingsReader: 
        :param multiData: 
        :return:
        """
        for fileElem in settingsReader.genTypeFile('gaze'):
            filePath = settingsReader.getPathAttrById('gaze', fileElem.get('id'), absolute=True)
            fileExt = os.path.splitext(filePath)[1]
            self.status_callback('Reading gaze data (' + os.path.basename(filePath) + ')...')
            if fileExt.lower()=='.tsv':
                self.status_callback('Parsing .tsv file.')
                # узнаем какие столбцы присутствуют
                headers = pd.read_table(filePath, nrows=1, encoding='UTF-16')
                availColumns = [i for i in list(headers.columns) if re.match('Recording timestamp|Gaze point|Gaze 3D position|Gaze direction|Pupil diameter|Eye movement type|Gaze event duration|Fixation point|Gyro|Accelerometer',i)]
                multiData.setNode('availColumns',fileElem.get('id'),availColumns)
                gazeData = pd.read_table(filePath, decimal=",", encoding='UTF-16',
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
                if multiData.hasAllColumns(['Gyro X','Gyro Y','Gyro Z','Accelerometer X','Accelerometer Y','Accelerometer Z'],fileElem.get('id')):
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
                    multiData.setNode('imu',fileElem.get('id'),gyro)

                    #FIXME doubled data
                    #gyro/accel
                    gyro = gazeData[['Recording timestamp','Gyro X', 'Gyro Y', 'Gyro Z']]
                    accel = gazeData[['Recording timestamp','Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]
                    # убираем пустые строки, но без учета столбца времени
                    gyro.dropna(subset=(['Gyro X', 'Gyro Y', 'Gyro Z']), how='all', inplace=True)
                    accel.dropna(subset=(['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']), how='all', inplace=True)
                    multiData.setNode('gyro', fileElem.get('id'), gyro)
                    multiData.setNode('accel',fileElem.get('id'), accel)

                    # гироскоп в основных данных больше не нужен
                    gazeData.drop(['Gyro X', 'Gyro Y', 'Gyro Z', 'Accelerometer X', 'Accelerometer Y', 'Accelerometer Z'], axis=1, inplace=True)
                else:
                    self.status_callback('No gyroscope/accelerometer data in file {0}!'.format(os.path.basename(filePath)))



                # убираем пустые строки
                gazeData = gazeData[(gazeData['Gaze point X'].notnull()) & (gazeData['Gaze point Y'].notnull()) | \
                                    (gazeData['Eye movement type'] == 'EyesNotFound')]


                if multiData.hasColumn('Eye movement type',fileElem.get('id')):
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
                    multiData.setNode('fixations',fileElem.get('id'),fixations)

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
                    multiData.setNode('saccades',fileElem.get('id'),saccades)


                    # участки потерянного контакта
                    eyesNotFounds = gazeData.loc[gazeData['Eye movement type'] == 'EyesNotFound'][['Recording timestamp',
                                                                                                   'Gaze event duration',
                                                                                                   'Eye movement type index']]
                    eyesNotFounds.drop_duplicates(eyesNotFounds.columns[range(1, eyesNotFounds.shape[1])], inplace=True)
                    multiData.setNode('eyesNotFounds',fileElem.get('id'),eyesNotFounds)

                    # неизвестные события
                    unclassifieds = gazeData.loc[gazeData['Eye movement type'] == 'Unclassified'][['Recording timestamp',
                                                                                                   'Gaze point X',
                                                                                                   'Gaze point Y',
                                                                                                   'Gaze event duration',
                                                                                                   'Eye movement type index']]
                    unclassifieds.drop_duplicates(unclassifieds.columns[range(1, unclassifieds.shape[1])], inplace=True)
                    multiData.setNode('unclassifieds',fileElem.get('id'),unclassifieds)


                    # события в основных данных больше не нужны
                    gazeData.drop(['Eye movement type', 'Gaze event duration', 'Eye movement type index',
                                   'Fixation point X', 'Fixation point Y'],
                                   axis=1, inplace=True)

                multiData.setNode('gaze',fileElem.get('id'),gazeData)
            #TODO
            elif fileExt.lower() == '.json':
                self.status_callback('WARNING: parsing .json files not implemented.')
            else:
                self.status_callback('Unknown file format.')




    #TODO catch exceptions in case of bad format
    #TODO parse and read voc_scores file type
    def read_voc(self, settingsReader, multiData) -> None:
        """Reads voc annotation from TextGrid file.

        :param settingsReader:
        :param multiData:
        :return:
        """
        for fileElem in settingsReader.genTypeFile('voc'):
            filePath=settingsReader.getPathAttrById('voc',fileElem.get('id'),absolute=True)
            fileExt = os.path.splitext(filePath)[1]
            self.status_callback('Reading voc annotation (' + os.path.basename(filePath) + ')...')
            if fileExt.lower() == '.textgrid':
                self.status_callback('Parsing .TextGrid file.')
                #WARNING: encoding hard-coded
                try:
                    vocData = TextGrid(filePath,codec='utf-16-be')
                except AttributeError:
                    self.status_callback('WARNING: Probably bad TextGrid. Switching to praatio module.')
                    self.status_callback('Try searching for newline characters in annotations.', color='warning')

                    try:
                        self.status_callback('Retrying with praatio.')
                        vocData=tgio.openTextgrid(filePath)
                    except:
                        self.status_callback('ERROR: Failed parsing TextGrid. Skipping file.')
                        return None
            else:
                self.status_callback('ERROR: Unknown file format.')

            multiData.setNode('voc', fileElem.get('id'), vocData)



    #TODO refactor all data read methods to callbacks with arguments of channel type
    def readManu(self, settingsReader, multiData) -> None:
        """Reads manu annotation from txt or eaf file.

        :param settingsReader: 
        :param multiData: 
        :return:
        """
        for fileElem in settingsReader.genTypeFile('manu'):
            filePath=settingsReader.getPathAttrById('manu',fileElem.get('id'),absolute=True)
            fileExt=os.path.splitext(filePath)[1]
            self.status_callback('Reading manu annotation (' + os.path.basename(filePath) + ')...')
            #TODO can refactor all such blocks to function calls after 'type' conditional
            if fileExt.lower()=='.eaf':
                self.status_callback('Parsing .eaf file.')
                manuData = Eaf(filePath)
            elif fileExt.lower()=='.txt':
                #FIXME need rename 'begin time' and 'duration' columns to be consistent with .eaf parsing
                self.status_callback('Parsing .txt file.')
                skiprows = self.determineSkiprows(filePath, '"#')
                manuData = pd.read_table(filePath, skiprows=skiprows)
                # названия столбцов не всегда одинаковые в разных записях
                manuData.rename(columns={col: re.sub('.*m.*gesture.*', 'mGesture', col, flags=re.IGNORECASE) for col in manuData.columns}, inplace=True)
                # manuData.rename(columns={col: re.sub('.*lt.*phases.*','mLtPhases',col,flags=re.IGNORECASE) for col in manuData.columns},inplace=True)
                # manuData.rename(columns={col: re.sub('.*rt.*phases.*', 'mRtPhases', col,flags=re.IGNORECASE) for col in manuData.columns},inplace=True)
            else:
                self.status_callback('ERROR: Unknown file format.')

            multiData.setNode('manu', fileElem.get('id'), manuData)



    def readCeph(self, settingsReader, multiData) -> None:
        """Reads ceph annotation from ELAN .eaf file.

        :param settingsReader:
        :param multiData:
        :return:
        """
        for fileElem in settingsReader.genTypeFile('ceph'):
            filePath=settingsReader.getPathAttrById('ceph',fileElem.get('id'),absolute=True)
            fileExt = os.path.splitext(filePath)[1]
            self.status_callback('Reading ceph annotation (' + os.path.basename(filePath) + ')...')
            if fileExt.lower() == '.eaf':
                self.status_callback('Parsing .eaf file.')
                cephData = Eaf(filePath)
            else:
                self.status_callback('ERROR: Unknown file format.')

            multiData.setNode('ceph', fileElem.get('id'), cephData)



    def readOcul(self, settingsReader, multiData) -> None:
        """Reads ocul annotation from Excel file.

        :param settingsReader: 
        :param multiData: 
        :return:
        """
        for fileElem in settingsReader.genTypeFile('ocul'):
            filePath=settingsReader.getPathAttrById('ocul',fileElem.get('id'),absolute=True)
            fileExt = os.path.splitext(filePath)[1]
            self.status_callback('Reading ocul annotation (' + os.path.basename(filePath) + ')...')
            if fileExt.lower() == '.eaf':
                self.status_callback('Parsing .eaf file.')
                oculData = Eaf(filePath)
            elif fileExt.lower() == '.xls':
                self.status_callback('Parsing .xls file.')
                oculData = pd.read_excel(filePath, header=None,
                                         #timecode should be the 1st column in current implementation
                                         names=('Begin_Time',
                                                'Duration',
                                                'E_Interlocutor', 'E_Localization'),
                                         usecols='B:E')
                # при считывании из excel в строках могут оставаться знаки \t
                oculData = oculData.applymap(lambda x: re.sub('\t(.*)', '\\1', str(x)))
                oculData = oculData.astype({'Duration': float},copy=False)
                oculData['Duration'] /= 1000
            else:
                self.status_callback('ERROR: Unknown file format.')

            multiData.setNode('ocul', fileElem.get('id'), oculData)




    def determineSkiprows(self, file: str, commentStr: str) -> int:
        """

        :param file: 
        :param commentStr: 
        :return: 
        """
        with open(file, encoding='UTF-8') as f:
            lineNum = 0
            line = f.readline()
            while line.startswith(commentStr):
                lineNum = lineNum + 1
                line = f.readline()
            return lineNum
