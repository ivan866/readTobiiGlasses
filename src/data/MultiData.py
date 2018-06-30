#from sys import getsizeof

from datetime import timedelta

from pandas import DataFrame

import pympi
import praatio


from SettingsReader import SettingsReader
from annotations import Annotations
from data import Utils



class MultiData():

    """Basic data structure to hold multidiscourse data.
    
    Includes some helper methods to select different data channels and filter by timestamp.
    """

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader = SettingsReader.getReader()
        self.multiData={}
        self.multiData['availColumns'] = {}
        self.multiData['voc'] = {}
        self.multiData['manu'] = {}
        self.multiData['ceph'] = {}
        self.multiData['ocul'] = {}
        self.multiData['gaze'] = {}
        self.multiData['fixations'] = {}
        self.multiData['saccades'] = {}
        self.multiData['eyesNotFounds'] = {}
        self.multiData['unclassifieds'] = {}
        self.multiData['imu'] = {}
        self.multiData['gyro'] = {}
        self.multiData['accel'] = {}
        self.empty = True


    # def __iter__(self,channel:str):
    #     """
    #
    #     :param channel: On which channel to iterate.
    #     :return:
    #     """
    #
    # #FIXME should return interface, not class
    # def __next__(self)->DataFrame:
    #     """
    #
    #     :return:
    #     """


    #TODO replace camelcase methods with underscores everywhere
    def genChannelIds(self,channel:str)->tuple:
        """Generator of ids present in multiData in particular channel.

        :param channel:
        :return: Tuple with current channel and id, if such id present in multiData.
        """
        if self.settingsReader.check() and self.check():
            channelZeroName = self.settingsReader.substGazeRelatedChannels(channel)
            for file in self.settingsReader.getTypes(channelZeroName):
                id=file.get('id')
                if self.hasChannelById(channel, id):
                    yield (channel, id)




    def reset(self)->None:
        """Makes this multiData empty.
        
        :return: None.
        """
        self.__init__(self.topWindow)

    def setNode(self, channel: str, id: str, data: object, recordId:str='defaultRecord') -> None:
        """Sets chosen node in hierarchy of multiData to given data object.
        
        :param channel: string of type from settings.
        :param id: string of channel id from settings.
        :param data: object with some data, probably pandas dataframe or python list.
        :param recordId: record id attribute value from settings file
        :return: 
        """
        self.topWindow.logger.debug('setting data node...')
        self.multiData[channel][id] = data
        self.empty=False


    #filter data methods
    #FIXME make channel/type/id arguments consistent across all code
    #but type is correct for settings file type, channel is correct for data channel
    def getChannelById(self, channel:str, id:str, format:str='as_is') -> object:
        """Returns what's inside multiData[channel][id] dict hierarchy, possibly converting to dataframe.
        
        :param channel: string of type from settings.
        :param id: string of channel id from settings.
        :param format: specify this str to convert to DataFrame type
        :return: data object, can be converted to dataframe.
        """
        self.topWindow.logger.debug('get channel by id')
        result=self.multiData[channel][id]
        if format=='dataframe':
            if type(result)==pympi.Elan.Eaf or type(result)==pympi.Praat.TextGrid or type(result)==praatio.tgio.Textgrid:
                return Annotations.parseAnnotationToDataframe(self.topWindow, result, settingsReader=self.settingsReader)
            elif type(result)==DataFrame:
                #self.topWindow.setStatus('Data object of type {0} of id {1} was already DataFrame. Returning as is.'.format(channel,id))
                return result
            else:
                self.topWindow.setStatus('WARNING: Converting this type of data to DataFrame not implemented.')
                return None
        elif format=='as_is':
            return result

    def getChannelAndTag(self, channel:str, id:str, format:str='as_is', ignoreEmpty:bool=True)->object:
        """Returns what's inside the given channel, but tags the data by record tag, id and interval first.
        
        :param channel: 
        :param id:
        :param format: str for type conversion
        :param ignoreEmpty: Whether to cut off the empty and utility intervals.
        :return: 
        """
        chData = self.getChannelById(channel, id, format=format)
        channelZeroName = self.settingsReader.substGazeRelatedChannels(channel)
        startFrom = self.settingsReader.getZeroTimeById(channelZeroName, id)
        pathAttr=self.settingsReader.getPathAttrById(type=channelZeroName,id=id)
        if ('Record tag' not in chData.columns) and ('Id' not in chData.columns):
            chData.insert(2, 'Record tag', pathAttr)
            chData.insert(3, 'Id', id)
        #FIXME hotfix
        elif 'Id 2' not in chData.columns:
            chData['Record tag']=pathAttr
            chData.insert(8, 'Id 2', id)
        #elif 'Id 3' not in chData.columns:
        #    chData.insert(9, 'Id 3', id)

        return self.tagIntervals(chData, startFrom, ignoreEmpty=ignoreEmpty)

    def getMeansByInterval(self,channel:str,id:str,interval:str):
        """Returns mean value of a channel in particular interval. Useful for calculating baseline noise in _static intervals.

        :param channel:
        :param id:
        :param interval: interval id to calculate on.
        :return: DataFrame with mean values for each column or None if specified interval does not exist.
        """
        data = self.getChannelAndTag(channel, id, ignoreEmpty=False)
        calculated=data.groupby(by=['Interval'], sort=False).agg(['mean'])
        if interval in calculated.index:
            return calculated.loc[interval, :]
        else:
            return None



    def getDataBetween(self,data:object,timeStart:object,timeEnd:object) -> object:
        """Selects and returns those data where timestamp is in given interval range.
        
        Assuming timestamp in column 0.
        
        :param data: data to trim from, usually after getChannelById method.
        :param timeStart: timestamp to begin data with in 'M:S.f' str or timedelta format.
        :param timeEnd: timestamp to end data with in 'M:S.f' str or timedelta format.
        :return: Trimmed data.
        """
        self.topWindow.logger.debug('get data between')
        #TODO determine where timestamp column is in data
        parsedTime=Utils.parseTimeV(data.iloc[:,0])
        try:
            data.insert(1,'Timedelta',parsedTime)
        except ValueError:
            pass

        if type(timeStart) is not timedelta:
            timeStart=Utils.parseTime(timeStart)
        if type(timeEnd) is not timedelta:
            timeEnd=Utils.parseTime(timeEnd)
        #TODO timedelta [:] indexing
        #TODO can use Series.between_time()
        return data.loc[(data['Timedelta']>=timeStart) & (data['Timedelta']<timeEnd)]

    def getDataInterval(self,data:object,startFrom:object,interval:str) -> object:
        """Selects and returns data where timestamp is inside interval defined by its id name.
        
        :param data: data to trim from, usually after getChannelById method.
        :param startFrom: Time value to start first interval from.
        :param interval: id of interval in str format from settings.
        :return: Trimmed data.
        """
        if type(startFrom) is not timedelta:
            startFrom=Utils.parseTime(startFrom)

        startTime=self.settingsReader.getStartTimeById(interval)+startFrom
        endTime = self.settingsReader.getEndTimeById(interval)+startFrom
        return self.getDataBetween(data,startTime,endTime)

    # def getDataFromAll(self,data:object,startFrom:object) -> object:
    #     """Selects and returns data from all intervals.
    #
    #     :param data: data to trim from, usually after getChannelById method.
    #     :param startFrom: Time value to start first interval from.
    #     :return: Data trimmed exactly to all your intervals.
    #     """
    #     self.topWindow.logger.debug('get data from all')
    #     if type(startFrom) is not timedelta:
    #         startFrom=Utils.parseTime(startFrom)
    #
    #     ints = self.settingsReader.getIntervals()
    #     intA = ints[0].get('id')
    #     intZ = ints[-1].get('id')
    #     startTime=self.settingsReader.getStartTimeById(intA)+startFrom
    #     endTime = self.settingsReader.getEndTimeById(intZ)+startFrom
    #     return self.getDataBetween(data,startTime,endTime)

    def tagIntervals(self, chData:object, startFrom:object, ignoreEmpty:bool=True)->DataFrame:
        """Tags given data by intervals, then returns a single dataframe.
        
        :param chData: data to stack intervals from, usually after getChannelById method.
        :param startFrom: zeroTime to start from.
        :param ignoreEmpty: Whether to cut off the empty and utility intervals.
        :return: DataFrame object ready to group by intervals.
        """
        data=[]
        ints=self.settingsReader.getIntervals(ignoreEmpty=ignoreEmpty)
        for interval in ints:
            intData=self.getDataInterval(chData, startFrom, interval.get('id'))
            intData.insert(4,'Interval',interval.get('id'))
            intData.insert(5,'Interval duration',interval.get('duration'))
            data.append(intData)

        #case when there is no interval block in settings at all - nothing to tag
        if len(ints)==0:
            return chData
        if len(ints)==1:
            data=data[0]
        else:
            data=data[0].append(data[1:])


        zeroBased=[]
        zeroTime=data.iloc[0,0]
        for timestamp in data.iloc[:,0]:
            zeroBased.append(timestamp-zeroTime)
        data.insert(1, 'TimestampZeroBased', zeroBased)

        return data





    def hasColumn(self,column:str,id:str) -> bool:
        """Checks if multiData contains such column in its gaze channel.
        
        :param column: Column name from Tobii gaze data.
        :param id: string of channel id from settings.
        :return: True if column present, False otherwise.
        """
        return column in self.multiData['availColumns'][id]

    def hasAllColumns(self,columns:list,id:str) -> bool:
        """Checks if multiData contains ALL these columns passed in list.
        
        :param columns: List of strings with column names.
        :param id: string of channel id from settings.
        :return: True if all columns present, False otherwise.
        """
        for col in columns:
            if col not in self.multiData['availColumns'][id]:
                return False
        return True


    def hasChannelById(self,channel:str,id:str) -> bool:
        """Checks if multiData contains this channel.id node in its hierarchy.
        
        :param channel: string of type from settings.
        :param id: string of channel id from settings.
        :return: True if such id in such channel present, False otherwise.
        """
        try:
            self.multiData[channel][id]
            return True
        except KeyError:
            return False




    def check(self) -> bool:
        """Helper method that checks if multiData present at all.
        
        :return: True if it is, False otherwise.
        """
        self.topWindow.logger.debug('check data')
        if not self.empty:
            return True
        else:
            self.topWindow.setStatus('WARNING: No data loaded yet. Read data first!')
            return False




    def validate(self) -> bool:
        """Performs some useful sanity checks on data for errors and integrity.
        
        For example, data is considered erratic if intervals in settings are out of range of actually loaded data 
        files, or there are two intervals with the same id, etc.
        
        :return: True if no errors found, False if data contains nonsense or mutually exclusive attributes.
        """
        #TODO issue #10
        #TODO проверить чтобы длины интервалов не выходили за пределы самой записи, а в статистике при этом должны выводиться фактические суммарные длительности, а не декларированные в настройках
        #TODO количество и длительности фиксаций в ocul и в gaze должны быть идентичны
        #что каждого id в каждом типе аннотаций только по 1 штуке
        pass