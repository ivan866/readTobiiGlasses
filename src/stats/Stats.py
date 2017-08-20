import os
from datetime import datetime

from tkinter import *

import xml.etree.ElementTree as ET

import pandas
from pandas import DataFrame
from pandas import Series

from SettingsReader import SettingsReader



class Stats():

    """Statistical methods for multidiscourse data."""

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
        self.topWindow.logger.debug('group by list and describe')
        if len(groupby):
            sliced = data.groupby(groupby, sort=False)[on].describe()
            slicedCountRat = sliced['count'] / sliced['count'].sum()
            slicedSum = data.groupby(groupby, sort=False)[on].sum()
            slicedSumRat = slicedSum / slicedSum.sum()
            sliced.insert(1, 'count ratio', value=slicedCountRat)
            sliced.insert(2, 'total', value=slicedSum)
            sliced.insert(3, 'total ratio', value=slicedSumRat)
            #считаем ratio по интервалам
            if ('Interval' in str(groupby)) and (type(groupby) is list and len(groupby)>1):
                ints=[int for int, *level in list(sliced.index)]
                slicedCountRatByInt=sliced['count'] / list(sliced['count'].groupby('Interval').sum()[ints])
                slicedSumRatByInt = slicedSum / list(slicedSum.groupby('Interval').sum()[ints])
                sliced.insert(2, 'count ratio by interval', value=slicedCountRatByInt)
                sliced.insert(5, 'total ratio by interval', value=slicedSumRatByInt)
        else:
            sliced = data[on].describe()
            slicedSum = data[on].sum()
            sliced=DataFrame(sliced).transpose()
            sliced.insert(1, 'total', value=slicedSum)

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
        now = datetime.now().strftime('%Y-%m-%d %H_%M_%S')
        dateTag = ET.Element('date')
        dateTag.text = now
        self.settingsReader.settings.append(dateTag)

        saveDir = self.settingsReader.dataDir + '/stats_' + now
        os.mkdir(saveDir)
        self.topWindow.logger.debug('iterating through data channels...')
        #статистика
        for channel in multiData.multiData['ocul']:
            chData=multiData.getChannelById('ocul', channel)
            startFrom=self.settingsReader.getZeroTimeById('ey',channel)
            #allData=multiData.getDataFromAll(data,startFrom)
            data=[]
            for interval in self.settingsReader.getIntervals():
                intData=multiData.getDataInterval(chData, startFrom, interval.get('id'))
                intData.insert(2,'Interval',interval.get('id'))
                data.append(intData)

            data=data[0].append(data[1:])

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('ocul',channel).get('path'))[0]+'_report.xls'
            self.saveIncrementally(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, 'Id', 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, data['Tier'].str.lower(), 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Interval', data['Tier'].str.lower()], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data, ['Id', data['Tier'].str.lower()], 'Gaze event duration'),
                                         self.groupbyListAndDescribe(data,['Interval', 'Id', data['Tier'].str.lower()],'Gaze event duration')])


        self.topWindow.logger.debug('writing settings...')
        self.settingsReader.settingsTree.write(saveDir + '/' + os.path.basename(self.settingsReader.settingsFile))

        reportFile=open(saveDir + '/history.txt','w')
        reportFile.write(self.topWindow.report.get('0.0',END))
        reportFile.close()

        self.topWindow.setStatus('Statistics reports saved. Settings included for reproducibility.')




    def save(self) -> None:
        """Writes calculated statistic to file."""
        pass