import os

import numpy

from scipy.stats import pearsonr
from scipy.stats import chisquare
from scipy.stats import fligner

import pandas
from pandas import DataFrame
from pandas import Series

from matplotlib import pyplot

from SettingsReader import SettingsReader



class Stats():

    """Statistical methods for multidiscourse data."""

    #TODO add sequence search for face-hands-face-hands patterns in ocul
    #TODO make test data package

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()


    def groupbyListAndDescribe(self,data:object,groupby:object,on:str)->DataFrame:
        """Slices data on groupby, aggregates on column and adds some descriptive columns.

        :param data: Dataframe to slice.
        :param groupby: List of columns or str to groupby, can be empty.
        :param on: Column to aggregate on.
        :return: data slice.
        """
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


    def save(self,file:str,data:list,sheets:list=[],serial:bool=False) -> None:
        """Writes calculated statistic to files.

        :param file: File path.
        :param data: List of DataFrame objects.
        :param sheets: List of sheet names.
        :param serial: Whether to save csv along with Excel files.
        :return:
        """
        if serial:
            self.saveCSV(file,data)
        self.saveIncrementally(file,data,sheets)

    def saveCSV(self,file:str,data:list)->None:
        """Writes stats to many csv, one for each table.

        :param file:
        :param data:
        :return:
        """
        dfNum = 0
        for df in data:
            dfNum = dfNum + 1
            fileInd = os.path.splitext(file)[0] + '_' + str(dfNum) + '.csv'
            # кодировка на случай кириллицы
            df.to_csv(fileInd, sep='\t', encoding='UTF-8')

    def saveIncrementally(self,file:str,data:list,sheets:list=[])->None:
        """Writes dataframes to one excel file, stacking them on the same sheet.

        :param file:
        :param data:
        :param sheets:
        :return:
        """
        self.topWindow.logger.debug('save incrementally')
        if len(sheets) and len(data)!=len(sheets):
            raise ValueError

        writer=pandas.ExcelWriter(file)
        dfNum=0
        startrow=0
        startrows={}
        for sheet in sheets:
            startrows[sheet]=0

        for df in data:
            if len(sheets):
                startrow=startrows[sheets[dfNum]]
                df.to_excel(writer, startrow=startrow, sheet_name=sheets[dfNum])
                startrows[sheets[dfNum]]=startrow+df.shape[0]+3
                dfNum=dfNum+1
            else:
                df.to_excel(writer, startrow=startrow)
                startrow = startrow + df.shape[0] + 3
            writer.save()



    def descriptive(self,multiData,dataExporter:object,serial:bool=False,savePath:str='') -> None:
        """Basic data summary.

        Data description, length, number of channels, etc. Means, medians and distributions, grouped by channels and overall.

        :param serial: If this is a serial batch.
        :return:
        """
        self.topWindow.logger.debug('descriptive stats')
        self.topWindow.setStatus('Gathering statistics... please wait.')
        saveDir=dataExporter.createDir(prefix='stats',serial=serial,savePath=savePath)
        self.topWindow.logger.debug('iterating through data channels...')


        #статистика
        if self.settingsReader.settings.find("interval[@id='']") is not None:
            self.topWindow.setStatus('Warning: unnamed intervals skipped!')

        for channel in multiData.multiData['fixations']:
            fData = multiData.getChannelAndTag('fixations', channel)
            #allData=multiData.getDataFromAll(chData,startFrom)

            sData = multiData.getChannelAndTag('saccades', channel)

            enfData = multiData.getChannelAndTag('eyesNotFounds', channel)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('gaze',channel).get('path'))[0]+'_report.xls'
            self.save(file,[self.groupbyListAndDescribe(fData, [], 'Gaze event duration'),
                            self.groupbyListAndDescribe(fData, 'Interval', 'Gaze event duration'),
                            self.groupbyListAndDescribe(sData, [], 'Gaze event duration'),
                            self.groupbyListAndDescribe(sData, 'Interval', 'Gaze event duration'),
                            self.groupbyListAndDescribe(enfData, [], 'Gaze event duration'),
                            self.groupbyListAndDescribe(enfData, 'Interval', 'Gaze event duration')],
                      sheets=['Fixations','Fixations','Saccades','Saccades','EyesNotFounds','EyesNotFounds'],
                      serial=serial)


        for channel in multiData.multiData['manu']:
            data = multiData.getChannelAndTag('manu', channel)
            #TODO проверить можно ли отбросить продублированные значения если не была снята галочка Repeat values of annotations
            data.dropna(subset=(['mGesture']), inplace=True)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('manu',channel).get('path'))[0]+'_report.xls'
            self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration - ss.msec'),
                            self.groupbyListAndDescribe(data, 'Interval', 'Duration - ss.msec')],
                      serial=serial)


        for channel in multiData.multiData['ocul']:
            data=multiData.getChannelAndTag('ocul',channel)

            file=saveDir + '/' + os.path.splitext(self.settingsReader.getTypeById('ocul',channel).get('path'))[0]+'_report.xls'
            self.save(file,[self.groupbyListAndDescribe(data, [], 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, 'Interval', 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, 'Id', 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, data['Tier'].str.lower(), 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, ['Interval', data['Tier'].str.lower()], 'Gaze event duration'),
                            self.groupbyListAndDescribe(data, ['Id', data['Tier'].str.lower()], 'Gaze event duration'),
                            self.groupbyListAndDescribe(data,['Interval', 'Id', data['Tier'].str.lower()],'Gaze event duration')],
                      serial=serial)




        self.topWindow.setStatus('Statistic reports saved.')
        dataExporter.copyMeta()



    def difference(self,pivotData:object)->None:
        """Statistical criteria applied to pivot tables.

        :param pivotData: PivotData object to apply to.
        :return:
        """
        #TODO
        self.topWindow.setStatus('--Difference statistics--')

        self.topWindow.setStatus('conv-manu-C+R-total ratio by duration')
        col=DataFrame(pivotData.pivots['manu'][1]['total ratio by duration'])
        col.reset_index(inplace=True)
        l1=col[(col['Id']=='C') & (col['Interval']=='conv')]['total ratio by duration']
        l3=col[(col['Id']=='R') & (col['Interval']=='conv')]['total ratio by duration']
        val=numpy.add(l1,l3)
        res=chisquare(val)
        self.topWindow.setStatus('chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic,res.pvalue))

        self.topWindow.setStatus('retell-manu-R-total ratio by duration')
        l3 = col[(col['Id']=='R') & (col['Interval']=='retell')]['total ratio by duration']
        res = chisquare(l3)
        self.topWindow.setStatus('chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic, res.pvalue))

        self.topWindow.setStatus('interval-duration ratio')
        col = DataFrame(pivotData.pivots['ocul'][1]['duration ratio'])
        col.reset_index(inplace=True)
        d = col[col['Id']=='N']
        datas=[]
        for tag,data in d.groupby('Record tag'):
            datas.append(list(data['duration ratio']))
        res=fligner(*datas)
        self.topWindow.setStatus('Fligner\'s chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic, res.pvalue))

        self.topWindow.setStatus('manu-interval-total ratio')
        col = DataFrame(pivotData.pivots['manu'][1]['total'])
        d=col.groupby(['Record tag', 'Interval']).sum()
        datas = []
        for tag, data in d.groupby('Record tag'):
            datas.append(list(data['total']))
        datas2=[]
        for el in datas:
            datas2.append(el/sum(el)*100)
        DataFrame(datas2).plot.bar(stacked=True)
        pyplot.title('Общая длительность жестикуляции')
        pyplot.xlabel('запись')
        pyplot.ylabel('общая длительность (%)')
        pyplot.xticks([0,1],[4,23])
        pyplot.legend(labels=['рассказ','разговор','пересказ'])
        pyplot.grid(True)
        pyplot.tight_layout()