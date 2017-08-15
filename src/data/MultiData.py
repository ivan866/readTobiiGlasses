from datetime import timedelta

from SettingsReader import SettingsReader

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
        self.multiData['gaze'] = {}
        self.multiData['fixations'] = {}
        self.multiData['saccades'] = {}
        self.multiData['eyesNotFounds'] = {}
        self.multiData['unclassifieds'] = {}
        self.multiData['gyro'] = {}
        self.multiData['accel'] = {}
        self.multiData['voc'] = {}
        self.multiData['manu'] = {}
        self.multiData['ceph'] = {}
        self.multiData['ocul'] = {}



    def setNode(self, channel: str, id: str, data: object) -> None:
        """Sets choosen node in hierarchy of multiData to given data object.
        
        :param channel: string of type from settings.
        :param id: string of channel id from settings.
        :param data: object with some data, probably pandas dataframe or python list.
        :return: 
        """
        self.multiData[channel][id] = data


    #filter data methods
    def getChannelById(self, channel:str, id:str) -> object:
        """Returns what's inside multiData[channel][id] dict hierarchy.
        
        :param channel: string of type from settings.
        :param id: string of channel id from settings.
        :return: data object.
        """
        return self.multiData[channel][id]


    def getDataBetween(self,data:object,timeStart:object,timeEnd:object) -> object:
        """Selects and returns those data where timestamp is in given interval range.
        
        Assuming timestamp in column 0.
        
        :param data: data to trim from, usually after getChannelById method.
        :param timeStart: timestamp to begin data with in 'M:S.f' str or timedelta format.
        :param timeEnd: timestamp to end data with in 'M:S.f' str or timedelta format.
        :return: Trimmed data.
        """
        #TODO determine where timestamp column is in data
        parsedTime=Utils.parseTimeV(data.iloc[:,0])
        data.insert(1,'Timedelta',parsedTime)

        if type(timeStart) is not timedelta:
            timeStart=Utils.parseTime(timeStart)
        if type(timeEnd) is not timedelta:
            timeEnd=Utils.parseTime(timeEnd)

        return data.iloc[(data['Timedelta']>=timeStart) & (data['Timedelta']<timeEnd)]

    def getDataInterval(self,data:object,interval:str) -> object:
        """Selects and returns data where timestamp is inside interval defined by its id name.
        
        :param data: data to trim from, usually after getChannelById method.
        :param interval: id of interval in str format from settings.
        :return: Trimmed data.
        """
        startTime=self.settingsReader.getStartTimeById(interval)
        endTime = self.settingsReader.getEndTimeById(interval)
        return self.getDataBetween(data,startTime,endTime)


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
        if self.multiData:
            return True
        else:
            self.topWindow.setStatus('Read data first.')
            return False


    def validate(self) -> bool:
        """Performs some useful sanity checks on data for errors and integrity.
        
        For example, data is considered erratic if intervals in settings are out of range of actually loaded data 
        files, or there are two intervals with the same id, etc.
        
        :return: True if no errors found, False if data contains nonsense or mutually exclusive attributes.
        """
        pass