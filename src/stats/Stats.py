import os
import sys

import numpy

import scipy
import scipy.stats
from scipy.stats import pearsonr
from scipy.stats import chisquare
from scipy.stats import fligner

import pandas
from pandas import DataFrame
from pandas import Series
from pandas.io.formats.style import Styler

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

import statsmodels



from SettingsReader import SettingsReader




#FIXME probably class not needed, only static funcitons
class Stats():

    """Statistical methods for multidiscourse data."""

    #TODO add sequence search for face-hands-face-hands patterns in ocul
    #TODO make test data package

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()




    def descriptive(self, multiData, dataExporter:object, serial:bool=False, savePath:str='') -> None:
        """Basic data summary.

        Data description, length, number of channels, etc. Means, medians and distributions, grouped by channels and overall.

        :param multiData:
        :param dataExporter:
        :param serial: If this is a serial batch.
        :param savePath:
        :return:
        """
        try:
            saveDir=dataExporter.createDir(prefix='stats', serial=serial, savePath=savePath)
        except ValueError:
            self.topWindow.reportError()
            return None

        #статистика
        self.topWindow.logger.debug('descriptive stats')
        self.topWindow.logger.debug('iterating through data channels...')
        self.topWindow.setStatus('Gathering statistics... please wait.')
        if self.settingsReader.settings.find("interval[@id='']") is not None:
            self.topWindow.setStatus('WARNING: Unnamed intervals skipped!')
        statsType='descriptive'



        #TODO saccade velocity, saccade length stats + binning, fixation dispersion
        messageShown=False
        for (channel, id) in multiData.genChannelIds(channel='fixations'):
            #TODO need refactor copies of this block
            channelZeroName=self.settingsReader.substGazeRelatedChannels(channel)
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channelZeroName))
                messageShown=True

            try:
                fData = multiData.getChannelAndTag(channel, id)
                #allData=multiData.getDataFromAll(chData,startFrom)
                sData = multiData.getChannelAndTag('saccades', id)
                enfData = multiData.getChannelAndTag('eyesNotFounds', id)
                uncData = multiData.getChannelAndTag('unclassifieds', id)

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channelZeroName, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(fData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, 'Interval', 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, 'Interval', 'Gaze event duration'),
                                self.groupbyListAndDescribe(enfData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(enfData, 'Interval', 'Gaze event duration'),
                                self.groupbyListAndDescribe(uncData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(uncData, 'Interval', 'Gaze event duration')],
                          sheets=['Fixations','Fixations','Saccades','Saccades','EyesNotFounds','EyesNotFounds','Unclassifieds','Unclassifieds'],
                          serial=serial)
            except AttributeError:
                self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel,id))
            except:
                self.topWindow.reportError()
                self.topWindow.setStatus('Skipping {0} channel for id {1}.'.format(channel,id),color='error')





        #TODO word category binning stats
        messageShown=False
        for (channel, id) in multiData.genChannelIds(channel='voc'):
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channel))
                messageShown = True
            try:
                data = multiData.getChannelAndTag(channel, id, format='dataframe')

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, 'Words', 'Duration'),
                                self.groupbyListAndDescribe(data, 'Supra', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Words', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Words', 'Supra'], 'Duration')],
                          serial=serial)
            #FIXME large duplicated try-except blocks, need refactor to method
            except AttributeError:
                self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel, id))
            except KeyError:
                self.topWindow.reportError()
                self.topWindow.setStatus('ERROR: Probably unknown tier name. Skipping {0} channel for id {1}.'.format(channel,id),color='error')
                #FIXME assumes file is .eaf without checking it
                self.topWindow.setStatus('Try searching for mistakes, typos and inconsistent naming schemes in .eaf.',color='error')
            except:
                self.topWindow.reportError()
                self.topWindow.setStatus('Skipping {0} channel for id {1}.'.format(channel, id),color='error')




        #TODO select needed tier combinations from XML or CLI, also possible to edit the GUI lists, after checking the GUI mode with warning
        #TODO FIXME на самом деле все поисковые запросы должны выполняться мелкими порциями через SQL-выражения, прописанные пачкой в .bat-файл или !!скрипт для MySQL
        messageShown=False
        for (channel, id) in multiData.genChannelIds(channel='manu'):
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channel))
                messageShown = True
            try:
                data = multiData.getChannelAndTag(channel, id, format='dataframe')
                # для расчета игнорируя уникальность индексов в нужном столбце
                data['mGesture'].replace(to_replace='(^.*mGe)\d+$', value='\\1', regex=True, inplace=True)
                data['mAdaptor'].replace(to_replace='(^.*mAd)\d+$', value='\\1', regex=True, inplace=True)
                data['mAdType'].replace(to_replace='.*', value='AnyAdType', regex=True, inplace=True)
                data['mAllGeStroke'].replace(to_replace='.*', value='AnyGeStroke', regex=True, inplace=True)
                #TODO проверить можно ли отбросить продублированные значения если не была снята галочка Repeat values of annotations
                #self.topWindow.setStatus('WARNING: only \'mGesture\' tier will be considered in current implementation.')
                #data.dropna(subset=(['mGesture']), inplace=True)

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mLtMtType', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mRtMtType', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mLtStType', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mRtStType', 'Duration'),
                                self.groupbyListAndDescribe(data, 'mGesture', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mGeHandedness', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mGeStructure', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mGeTags', 'Duration'),
                                #self.groupbyListAndDescribe(data, 'mGeFunction', 'Duration'),
                                self.groupbyListAndDescribe(data, 'mAdaptor', 'Duration'),
                                self.groupbyListAndDescribe(data, 'mAdType', 'Duration'),
                                #self.groupbyListAndDescribe(data, ['mAdaptor', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, 'mLtGeStroke', 'Duration'),
                                self.groupbyListAndDescribe(data, 'mRtGeStroke', 'Duration'),
                                self.groupbyListAndDescribe(data, 'mAllGeStroke', 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mLtMtType'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mRtMtType'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mLtStType'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGesture'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mGeHandedness'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mGeStructure'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mGeTags'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAdType'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mAdaptor', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAllGeStroke'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mLtGeStroke', 'mRtGeStroke', 'mAllGeStroke'], 'Duration'),
                                #self.groupbyListAndDescribe(data, ['Interval', 'mGeHandedness','mGeStructure','mGeTags','mGeFunction'], 'Duration')
                    ],
                          serial=serial)
            except AttributeError:
                self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel,id))
            except KeyError:
                self.topWindow.reportError()
                self.topWindow.setStatus('ERROR: Probably unknown tier name. Skipping {0} channel for id {1}.'.format(channel,id),color='error')
                self.topWindow.setStatus('Try searching for mistakes, typos and inconsistent naming schemes in .eaf.',color='error')
            except:
                self.topWindow.reportError()
                self.topWindow.setStatus('Skipping {0} channel for id {1}.'.format(channel,id),color='error')




        #FIXME need ignore NaNs during groupby, and blank fields must be nans too
        messageShown=False
        for (channel, id) in multiData.genChannelIds(channel='ceph'):
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channel))
                messageShown = True
            data = multiData.getChannelAndTag(channel, id, format='dataframe')

            try:
                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, 'cMoveType', 'Duration'),
                                self.groupbyListAndDescribe(data, 'cTags', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'cMoveType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'cTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['cMoveType', 'cTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'cMoveType', 'cTags'], 'Duration')],
                          serial=serial)
            except AttributeError:
                self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel,id))
            except KeyError:
                self.topWindow.reportError()
                self.topWindow.setStatus('ERROR: Probably unknown tier name. Skipping {0} channel for id {1}.'.format(channel,id),color='error')
                self.topWindow.setStatus('Try searching for mistakes, typos and inconsistent naming schemes .eaf.',color='error')
            except:
                self.topWindow.reportError()
                self.topWindow.setStatus('Skipping {0} channel for id {1}.'.format(channel,id),color='error')




        messageShown=False
        for (channel, id) in multiData.genChannelIds(channel='ocul'):
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channel))
                messageShown = True

            try:
                data=multiData.getChannelAndTag(channel, id, format='dataframe')
                #FIXME временный 'костыль', пока не поправят в исходниках аннотаций
                data.rename(columns={'E_Locus': 'E_Localization'}, inplace=True)

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, 'E_Interlocutor', 'Duration'),
                                self.groupbyListAndDescribe(data, data['E_Localization'].str.lower(), 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', data['E_Localization'].str.lower()], 'Duration'),
                                self.groupbyListAndDescribe(data, ['E_Interlocutor', data['E_Localization'].str.lower()], 'Duration'),
                                self.groupbyListAndDescribe(data,['Interval', 'E_Interlocutor', data['E_Localization'].str.lower()],'Duration')],
                          serial=serial)
            except AttributeError:
                self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel,id))
            except KeyError:
                self.topWindow.reportError()
                self.topWindow.setStatus('ERROR: Probably unknown tier name. Skipping {0} channel for id {1}.'.format(channel,id),color='error')
                self.topWindow.setStatus('Try searching for mistakes, typos and inconsistent naming schemes in .eaf.',color='error')
            except:
                self.topWindow.reportError()
                self.topWindow.setStatus('Skipping {0} channel for id {1}.'.format(channel,id),color='error')





        self.topWindow.setStatus('Descriptive statistic reports saved to {0}.'.format(saveDir),color='success')
        dataExporter.copyMeta()





    def difference(self,pivotData:object)->None:
        """Statistical criteria applied to pivot tables.

        :param pivotData: PivotData object to apply to.
        :return:
        """
        #TODO
        # self.topWindow.setStatus('--Difference statistics--')
        #
        # self.topWindow.setStatus('conv-manu-C+R-total ratio by duration')
        # col=DataFrame(pivotData.pivots['manu'][1]['total ratio by duration'])
        # col.reset_index(inplace=True)
        # l1=col[(col['Id']=='C') & (col['Interval']=='conv')]['total ratio by duration']
        # l3=col[(col['Id']=='R') & (col['Interval']=='conv')]['total ratio by duration']
        # val=numpy.add(l1,l3)
        # res=chisquare(val)
        # self.topWindow.setStatus('chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic,res.pvalue))
        #
        # self.topWindow.setStatus('retell-manu-R-total ratio by duration')
        # l3 = col[(col['Id']=='R') & (col['Interval']=='retell')]['total ratio by duration']
        # res = chisquare(l3)
        # self.topWindow.setStatus('chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic, res.pvalue))
        #
        # self.topWindow.setStatus('interval-duration ratio')
        # col = DataFrame(pivotData.pivots['ocul'][1]['duration ratio'])
        # col.reset_index(inplace=True)
        # d = col[col['Id']=='N']
        # datas=[]
        # for tag,data in d.groupby('Record tag'):
        #     datas.append(list(data['duration ratio']))
        # res=fligner(*datas)
        # self.topWindow.setStatus('Fligner\'s chi sq.={0:.3f}, p={1:.2f}'.format(res.statistic, res.pvalue))
        #
        # self.topWindow.setStatus('manu-interval-total ratio')
        # col = DataFrame(pivotData.pivots['manu'][1]['total'])
        # d=col.groupby(['Record tag', 'Interval']).sum()
        # datas = []
        # for tag, data in d.groupby('Record tag'):
        #     datas.append(list(data['total']))
        # datas2=[]
        # for el in datas:
        #     datas2.append(el/sum(el)*100)
        # DataFrame(datas2).plot.bar(stacked=True)
        # pyplot.title('Общая длительность жестикуляции')
        # pyplot.xlabel('запись')
        # pyplot.ylabel('общая длительность (%)')
        # pyplot.xticks([0,1],[4,23])
        # pyplot.legend(labels=['рассказ','разговор','пересказ'])
        # pyplot.grid(True)
        # pyplot.tight_layout()
        pass




    #TODO subplotting
    #TODO refactor all plot types to viz/methods
    #  это позволит и видоизменять язык надписей без труда, и цвета
    #TODO export plot data to standard format
    #TODO bokeh html interactive output
    #  tools=, tooltips=
    #  figure.line(, line_color="#FF0000", line_width=8, alpha=0.7, legend="PDF")
    #  figure.legend.location='center_right'
    #  figure.legend.background_fill_color='darkgrey'
    def ANOVA_stats(self, multiData:object, pivotData:object, dataExporter:object)->None:
        """Analysis of variance on distribution data.

        Combinations to include in cross-table must be specified.

        :param multiData: multiData struct with different data channels, unpivoted and ungrouped.
        :param pivotData: ??needed?   pivoted data, mainly after running 'Batch and pivot'.
        :param dataExporter:
        :return:
        """
        self.topWindow.setStatus('ANOVA requested.')
        #self.topWindow.setStatus('Standardizing to z-scores.')
        #проверить есть ли разница в величине f-теста с и без z-score
        #zdata1=scipy.stats.zscore(data1, axis=0)

        self.topWindow.setStatus('Sample size and distribution requirements.')
        #statsmodels.stats.power.FTestAnovaPower.power
        #number of modes ??function
        #проверка сбалансированности измерений
        # kernel1=scipy.stats.gaussian_kde(data1, bw_method='scott')
        # kernel2=scipy.stats.gaussian_kde(data2, bw_method='scott')
        # xs=numpy.linspace(min(data1),max(data1),100)
        # plt.plot(xs,kernel1(xs))
        # plt.plot(xs,kernel2(xs))
        plt.title('Плотность распределения')
        plt.xlabel('Длительность (с)')
        plt.ylabel('Плотность')
        #plt.axes().set_major_locator(plt.MaxNLocator(10))
        #plt.minorticks_on()
        plt.hist(data1, bins=20, density=True, cumulative=False, orientation='vertical', rwidth=0.5, color=None)    #bins='auto'
        #plt.hist(data2, bins=20, density=True, cumulative=False, orientation='vertical')
        #sns.kdeplot(norm_distr_for_data.pdf(xs), bw=0.15, shade=False, vertical=False, gridsize=100, legend=True, cumulative=False)  #kdeplot(data1, data2)
        plt.plot(xs, plt.ylim()[1]*norm_distr_for_data.pdf(xs))
        sns.kdeplot(data1, bw=0.15, shade=False, vertical=False, gridsize=100, legend=True, cumulative=False)  #kdeplot(data1, data2)
        sns.kdeplot(data1, bw=0.15, shade=False, vertical=False, gridsize=100, legend=True, cumulative=True)  #kdeplot(data1, data2)
        #sns.kdeplot(data2, bw=0.15)
        #plt.grid()

        #scipy.stats.norm.rvs(size=100)
        sns.kdeplot(data1, bw=0.15, cumulative=True)  #kdeplot(data1, data2)
        sns.kdeplot(data2, bw=0.15)
        # Q-Q plot
        #plt.scatter()
        #scipy.stats.norm.rvs(size=100)
        loc, scale = scipy.stats.norm.fit(data1)
        norm_distr_for_data=scipy.stats.norm(loc=loc, scale=scale)
        scipy.stats.kstest(data1, norm_distr_for_data.cdf)
        scipy.stats.levene(zdata1,zdata2)

        self.topWindow.setStatus('F-test:')
        sample1=multiData.getChannelAndTag('ocul','N', format='dataframe')
        data1=sample1.loc[sample1['Interval']=='01_tell','Duration']
        sample2=multiData.getChannelAndTag('ocul','R', format='dataframe')
        data2=sample2.loc[sample2['Interval']=='01_tell','Duration']
        scipy.stats.f_oneway(zdata1,zdata2)


        #effect size
        #scheffe test

        self.topWindow.setStatus('Distributional plots...')
        #plt.bar()
        #with sns.axes_style('darkgrid'):
        #    sns.barplot(, estimator=sum, hue='')
        #scipy.stats.binned_statistic(, statistic='count', bins=10)
        #data1.hist(bins=10)
        plt.hist(data1, bins='auto', density=False, cumulative=True, orientation='vertical')
        #scipy.stats.cumfreq(, numbins=10)
        #plt.boxplot(data2, notch=True, sym='.', vert=True)   #labels=[]
        #sns.swarmplot()
        #dataframe.boxplot(,by=,figsize=(8,6))
        #Q-Q plot можно для разных переменных, чтобы видеть профиль и сравнивать
        #plt.errorbar()
        #plt.savefig()






    #FIXME interval sort order must be always unsorted
    #TODO must refactor all describe logic to separate method
    #TODO can factor out returned dataframes from multidata to special inherited and extended class, e.g. DataChannel
    #  который будет иметь hooks на методы обсчета статистики и возвращать нужные groupedby таблицы
    #  это позволит делать method chaining через точку
    #TODO all channels go to single .xls in different sheets
    def groupbyListAndDescribe(self, data:object, groupby:object, on:str) -> DataFrame:
        """Slices data on groupby, aggregates on column and adds some descriptive columns.

        :param data: Dataframe to slice.
        :param groupby: List of columns or str to groupby, can be empty.
        :param on: Column to aggregate on.
        :return: data slice.
        """
        self.topWindow.logger.debug('group by list and describe')
        #data.fillna('<NA>',inplace=True)
        if type(groupby) is str:
            groupby=[groupby]
        if len(groupby):
            #TODO добавить визуализации в виде мелких гистограмм для квартилей в этой статистике
            grouped=data.groupby(groupby, sort=False)
            onned=grouped[on]
            #describe() gets exception if len(grouped.indices)==1
            agg1=onned.agg(['count','sum','mean','std','min'])
            #FIXME duplicate value list, can set it in ?settings file
            agg2=onned.agg('quantile',q=[0.25,0.5,0.75])
            #FIXME? empty agg2 still contains wrong column names because not unstacked
            if len(agg2):
                #принудительно сортируется индекс
                agg2=agg2.unstack()
            agg3=onned.agg(['max'])
            sliced=pandas.concat([agg1,agg2,agg3],axis=1)#,sort=False,copy=False)
            #возвращаем порядок (интервалов) как был исходно (во второй таблице не работает)
            #sliced=sliced.reindex(index=onned.indices, copy=False)
            sliced.sort_index(inplace=True)
            slicedCountRat = sliced['count'] / sliced['count'].sum()
            slicedSumRat = sliced['sum'] / sliced['sum'].sum()
            sliced.insert(1, 'count ratio', value=slicedCountRat)
            sliced.insert(3, 'sum ratio', value=slicedSumRat)
            # считаем ratio от длительности интервала
            if ('Interval' in str(groupby)) and (len(groupby) == 1):
                recordDur = self.settingsReader.totalDuration()
                #не все интервалы могут присутствовать в срезе
                durs=[]
                for interval in list(sliced.index):
                    durs.append(self.settingsReader.getDurationById(interval))
                durs=Series(durs)/numpy.timedelta64(1,'s')
                durs.index = sliced.index
                slicedTotalRatByDur = sliced['sum'] / durs
                sliced.insert(0, 'duration', value=durs)
                sliced.insert(1, 'duration ratio', value=durs/recordDur.total_seconds())
                sliced.insert(6, 'sum ratio by duration', value=slicedTotalRatByDur)
            #считаем ratio по интервалам
            elif ('Interval' in str(groupby)) and (len(groupby)>1):
                ints=[int for int, *level in list(sliced.index)]
                slicedCountRatByInt=sliced['count'] / list(sliced['count'].groupby('Interval').sum()[ints])
                slicedSumRatByInt = sliced['sum'] / list(sliced['sum'].groupby('Interval').sum()[ints])
                sliced.insert(2, 'count ratio by interval', value=slicedCountRatByInt)
                sliced.insert(5, 'sum ratio by interval', value=slicedSumRatByInt)
        else:
            onned=data[on]
            agg1 = onned.agg(['count', 'sum', 'mean', 'std', 'min'])
            agg2 = onned.agg('quantile', q=[0.25, 0.5, 0.75])
            agg3 = onned.agg(['max'])
            sliced = pandas.concat([agg1, agg2, agg3])
            sliced=DataFrame(sliced).transpose()
            recordDur=self.settingsReader.totalDuration()
            sliced.insert(0, 'duration', value=recordDur.total_seconds())

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
            #st = Styler(df, precision=3)
            #st.background_gradient()
            #st.highlight_max()
            #st.highlight_min()
            #st.highlight_null()
            if len(sheets):
                startrow=startrows[sheets[dfNum]]
                df.to_excel(writer, startrow=startrow, sheet_name=sheets[dfNum])
                #st.to_excel(writer, startrow=startrow, sheet_name=sheets[dfNum])
                startrows[sheets[dfNum]]=startrow+df.shape[0]+3
                dfNum=dfNum+1
            else:
                if len(df):
                    self.topWindow.logger.debug('writing xls file')
                    df.to_excel(writer, startrow=startrow)
                    #st.to_excel(writer, startrow=startrow)
                    startrow = startrow + df.shape[0] + 3
                else:
                    self.topWindow.setStatus('WARNING: Empty table encountered in file {0}. Omitting from report.'.format(os.path.basename(file)))

            writer.save()