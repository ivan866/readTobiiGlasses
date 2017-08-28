import os
from datetime import datetime

from tkinter import *

import xml.etree.ElementTree as ET

import numpy

import pandas
from pandas import DataFrame
from pandas import Series

from SettingsReader import SettingsReader



class Stats():

    """Statistical methods for multidiscourse data."""

    #TODO add sequence search for face-hands-face-hands patterns in ocul

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()


    def groupbyListAndDescribe(self,data:object,groupby:object,on=str)->DataFrame:
        """Slices data on groupby, aggregates on column and adds some descriptive columns.
        
        :param data: Dataframe to slice.
        :param groupby: List of columns or str to groupby, can be empty.
        :param on: Column to aggregate on.
        :return: data slice.
        """
        #TODO отбрасывать интервалы trans?
        #TODO change describe to agg(count,sum,etc.)
        self.topWindow.logger.debug('group by list and describe')
        #data.fillna('<NA>',inplace=True)
        if type(groupby) is str:
            groupby=[groupby]
        if len(groupby):
            sliced = data.groupby(groupby, sort=False)[on].describe()
            slicedCountRat = sliced['count'] / sliced['count'].sum()
            slicedSum = data.groupby(groupby, sort=False)[on].sum()
            slicedSumRat = slicedSum / slicedSum.sum()
            sliced.insert(1, 'count ratio', value=slicedCountRat)
            sliced.insert(2, 'total', value=slicedSum)
            sliced.insert(3, 'total ratio', value=slicedSumRat)
            # считаем ratio от длительности интервала
            if ('Interval' in str(groupby)) and (len(groupby) == 1):
                recordDur = self.settingsReader.totalDuration()
                #не все интервалы могут присутствовать в срезе
                durs=[]
                for interval in list(sliced.index):
                    durs.append(self.settingsReader.getDurationById(interval))
                durs=Series(durs)/numpy.timedelta64(1,'s')
                durs.index = sliced.index
                slicedTotalRatByDur = sliced['total'] / durs
                sliced.insert(0, 'duration', value=durs)
                sliced.insert(1, 'duration ratio', value=durs/recordDur.total_seconds())
                sliced.insert(6, 'total ratio by duration', value=slicedTotalRatByDur)
            #считаем ratio по интервалам
            elif ('Interval' in str(groupby)) and (len(groupby)>1):
                ints=[int for int, *level in list(sliced.index)]
                slicedCountRatByInt=sliced['count'] / list(sliced['count'].groupby('Interval').sum()[ints])
                slicedSumRatByInt = slicedSum / list(slicedSum.groupby('Interval').sum()[ints])
                sliced.insert(2, 'count ratio by interval', value=slicedCountRatByInt)
                sliced.insert(5, 'total ratio by interval', value=slicedSumRatByInt)
        else:
            sliced = data[on].describe()
            slicedSum = data[on].sum()
            sliced=DataFrame(sliced).transpose()
            recordDur=self.settingsReader.totalDuration()
            sliced.insert(0, 'duration', value=recordDur.total_seconds())
            sliced.insert(2, 'total', value=slicedSum)

        return sliced

    def saveIncrementally(self,file:str,data:list)->None:
        """Writes dataframes to one excel file, stacking them on the same sheet.
        
        :param file: File path.
        :param data: List of DataFrame objects.
        :return: 
        """
        self.topWindow.logger.debug('save incrementally')
        writer=pandas.ExcelWriter(file)
        startrow=0
        for df in data:
            df.to_excel(writer,startrow=startrow)
            startrow=startrow+df.shape[0]+3
            writer.save()


    def descriptive(self,multiData) -> None:
        """Basic data summary.
        
        Data description, length, number of channels, etc. Means, medians and distributions, grouped by channels and overall.
        
        :return: 
        """
        self.topWindow.logger.debug('descriptive stats')
        self.topWindow.setStatus('Gathering statistics... please wait.')
        now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
        dateTag = ET.Element('date')
        dateTag.text = now
        self.settingsReader.settings.append(dateTag)

        saveDir = self.settingsReader.dataDir + '/stats_' + now
        os.mkdir(saveDir)
        self.topWindow.logger.debug('iterating through data channels...')


        #статистика
        for channel in multiData.multiData['fixations']:
            chData = multiData.getChannelById('fixations', channel)
            startFrom = self.settingsReader.getZeroTimeById('ey', channel)
            #allData=multiData.getDataFromAll(chData,startFrom)
            data=multiData.tagIntervals(chData,startFrom)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('gaze',channel).get('path'))[0]+'_fixations report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration')])

        for channel in multiData.multiData['saccades']:
            chData = multiData.getChannelById('saccades', channel)
            startFrom = self.settingsReader.getZeroTimeById('ey', channel)
            data=multiData.tagIntervals(chData,startFrom)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('gaze',channel).get('path'))[0]+'_saccades report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration')])

        for channel in multiData.multiData['eyesNotFounds']:
            chData = multiData.getChannelById('eyesNotFounds', channel)
            startFrom = self.settingsReader.getZeroTimeById('ey', channel)
            data=multiData.tagIntervals(chData,startFrom)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('gaze',channel).get('path'))[0]+'_eyesNotFounds report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration')])


        for channel in multiData.multiData['manu']:
            chData=multiData.getChannelById('manu', channel)
            data = multiData.tagIntervals(chData, 0)
            #TODO проверить можно ли отбросить продублированные значения если не была снята галочка Repeat values of annotations
            data.dropna(subset=(['mGesture']), inplace=True)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('manu',channel).get('path'))[0]+'_report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Duration - ss.msec'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Duration - ss.msec')])


        for channel in multiData.multiData['ocul']:
            chData=multiData.getChannelById('ocul', channel)
            startFrom = self.settingsReader.getZeroTimeById('ey', channel)
            data = multiData.tagIntervals(chData, startFrom)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('ocul',channel).get('path'))[0]+'_report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Id', 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, data['Tier'].str.lower(), 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Interval', data['Tier'].str.lower()], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Id', data['Tier'].str.lower()], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data,['Interval', 'Id', data['Tier'].str.lower()],'Gaze event duration')])



        #TODO copy log here
        self.topWindow.logger.debug('writing settings...')
        self.settingsReader.settingsTree.write(saveDir + '/' + os.path.basename(self.settingsReader.settingsFile))

        self.topWindow.setStatus('Statistics reports saved. Settings included for reproducibility.')

        reportFile=open(saveDir + '/history.txt','w')
        reportFile.write(self.topWindow.report.get('0.0',END))
        reportFile.close()

        




    def save(self) -> None:
        """Writes calculated statistic to file."""
        pass