import os
from datetime import datetime

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

import plotly.offline as py
import plotly.graph_objs as go
from plotly import tools
import plotly.figure_factory as ff
#py.init_notebook_mode(connected=True)


import statsmodels



from SettingsReader import SettingsReader
from data import Utils




#FIXME probably class not needed, only static funcitons
class Stats():

    """Statistical methods for multidiscourse data."""

    #TODO add sequence search for face-hands-face-hands patterns in ocul
    #TODO make test data package

    def __init__(self,topWindow):
        self.topWindow = topWindow
        self.settingsReader=SettingsReader.getReader()

        # количество экспортируемых таблиц со статистикой
        #self.groupedByNum = 0




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
                self.topWindow.setStatus('Now doing gaze ({0}, etc.) channel.'.format(channelZeroName))
                messageShown=True

            try:
                fData = multiData.getChannelAndTag(channel, id)
                sData = multiData.getChannelAndTag('saccades', id)
                enfData = multiData.getChannelAndTag('eyesNotFounds', id)
                uncData = multiData.getChannelAndTag('unclassifieds', id)

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channelZeroName, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(fData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, 'Id', 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, 'Id 2', 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, ['Id', 'Id 2'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, 'Interval', 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, ['Interval', 'Id'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, ['Interval', 'Id 2'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(fData, ['Interval', 'Id', 'Id 2'], 'Gaze event duration'),

                                self.groupbyListAndDescribe(sData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, 'Id', 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, 'Id 2', 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, ['Id', 'Id 2'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, 'Interval', 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, ['Interval', 'Id'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, ['Interval', 'Id 2'], 'Gaze event duration'),
                                self.groupbyListAndDescribe(sData, ['Interval', 'Id', 'Id 2'], 'Gaze event duration'),

                                self.groupbyListAndDescribe(enfData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(enfData, 'Interval', 'Gaze event duration'),

                                self.groupbyListAndDescribe(uncData, [], 'Gaze event duration'),
                                self.groupbyListAndDescribe(uncData, 'Interval', 'Gaze event duration')
                                ],
                          sheets=['Fixations','Fixations','Fixations','Fixations','Fixations','Fixations','Fixations','Fixations',
                                  'Saccades','Saccades','Saccades','Saccades','Saccades','Saccades','Saccades','Saccades',
                                  'EyesNotFounds','EyesNotFounds',
                                  'Unclassifieds','Unclassifieds'
                                  ],
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
                data['EDU'].replace(to_replace='.*', value='AnyEDU', regex=True, inplace=True)
                data['Words'].replace(to_replace='\w+', value='AnyWord', regex=True, inplace=True)
                data['Words'].replace(to_replace='\([^ɥ.]+\)', value='(Any_ɯ)', regex=True, inplace=True)
                data['Words'].replace(to_replace='#.+#', value='Any_#', regex=True, inplace=True)
                data['Words'].replace(to_replace='{laugh}', value='laugh', regex=True, inplace=True)
                data['Words'].replace(to_replace='{.+}', value='Any_{}', regex=True, inplace=True)

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id', 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id 2', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'EDU', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'EDU'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'EDU'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'Words', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'Words'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'Supra', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'Supra'], 'Duration'),

                                self.groupbyListAndDescribe(data, ['EDU', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['EDU', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Words', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'EDU', 'Words'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'EDU', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Words', 'Supra'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'EDU', 'Words', 'Supra'], 'Duration')
                                ],
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




        #TODO все descriptive тоже надо положить в один xls в разные листы
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
                data['mGesture'].replace(to_replace='^.*(mGe)\d+$', value='\\1', regex=True, inplace=True)
                data['mAdaptor'].replace(to_replace='^.*(mAd)\d+$', value='\\1', regex=True, inplace=True)
                data['mAdType'].replace(to_replace='.*', value='AnyAdType', regex=True, inplace=True)
                data['mAllGeStroke'].replace(to_replace='.*', value='AnyGeStroke', regex=True, inplace=True)

                #TODO проверить можно ли отбросить продублированные значения если не была снята галочка Repeat values of annotations
                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id', 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id 2', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mLtMtType', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mLtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mLtMtType'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mRtMtType', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mRtMtType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mRtMtType'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mLtStType', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mLtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mLtStType'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mRtStType', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mRtStType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mRtStType'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mGesture', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mGesture'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mGesture'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mGeHandedness', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mGeHandedness'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mGeHandedness'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mGeStructure', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mGeStructure'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mGeStructure'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mGeStructure'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGeStructure'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mGeStructure'],'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mGeStructure'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mGeStructure'],'Duration'),

                                self.groupbyListAndDescribe(data, 'mGeTags', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mGeTags'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mGeTags'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mGeFunction', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mGeFunction'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mGeFunction'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mAdaptor', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mAdaptor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mAdaptor'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mAdType', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mAdType'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mAdType'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mLtGeStroke', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mLtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mLtGeStroke'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mRtGeStroke', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mRtGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mRtGeStroke'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'mAllGeStroke', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'mAllGeStroke'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'mAllGeStroke'], 'Duration'),
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
                #data.rename(columns={'E_Locus': 'E_Localization'}, inplace=True)
                dataLowered=data['E_Localization'].str.lower()

                file='{0}/{1}_{2}.xls'.format(saveDir,self.settingsReader.getPathAttrById(channel, id),statsType)
                self.save(file,[self.groupbyListAndDescribe(data, [], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id', 'Duration'),
                                self.groupbyListAndDescribe(data, 'Id 2', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, 'Interval', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2'], 'Duration'),

                                self.groupbyListAndDescribe(data, 'E_Interlocutor', 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', 'E_Interlocutor'], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', 'E_Interlocutor'], 'Duration'),

                                self.groupbyListAndDescribe(data, dataLowered, 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id 2', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Id', 'Id 2', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id 2', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'Id', 'Id 2', dataLowered], 'Duration'),

                                self.groupbyListAndDescribe(data, ['E_Interlocutor', dataLowered], 'Duration'),
                                self.groupbyListAndDescribe(data, ['Interval', 'E_Interlocutor', dataLowered],'Duration')
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




        #----
        #SPECIAL TYPES
        messageShown = False
        for (channel, id) in multiData.genChannelIds(channel='manu-voc-tempo'):
            if not messageShown:
                self.topWindow.setStatus('Now doing {0} channel.'.format(channel))
                messageShown = True
            try:
                data = multiData.getChannelAndTag(channel, id, format='dataframe')
                #делим данные по типам событий
                dataGesture = data.loc[data['EventType']=='Gesture']
                dataGeStroke = data.loc[data['EventType']=='GeStroke']
                dataEDU = data.loc[data['EventType']=='EDU']
                dataFRG = data.loc[data['EventType']=='FRG']

                file = '{0}/{1}_{2}.xls'.format(saveDir, self.settingsReader.getPathAttrById(channel, id), statsType)
                #TODO the sequence can be generated as samples from the set without ?repeat, all possible combinations, the empty ones will be automatically omitted
                self.save(file, [self.groupbyListAndDescribe(dataGesture, [], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Id', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGesture, ['Interval', 'Id', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),

                                 self.groupbyListAndDescribe(dataGeStroke, [], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Id', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id', 'Id 2'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),
                                 self.groupbyListAndDescribe(dataGeStroke, ['Interval', 'Id', 'Id 2', 'LenType'], ['Duration', 'TimeProp']),

                                 self.groupbyListAndDescribe(dataEDU, [], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Id', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataEDU, ['Interval', 'Id', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),

                                 self.groupbyListAndDescribe(dataFRG, [], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Id', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id', 'Id 2'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo']),
                                 self.groupbyListAndDescribe(dataFRG, ['Interval', 'Id', 'Id 2', 'TempoType'], ['Duration', 'TimeProp', 'Tempo'])
                                 ],
                          sheets=['Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture', 'Gesture',
                                  'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke', 'GeStroke',
                                  'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU', 'EDU',
                                  'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG', 'FRG'],
                          serial=serial)
            #except AttributeError:
            #    self.topWindow.setStatus('ERROR: Probably bad or no data. Skipping {0} channel for id {1}.'.format(channel, id))
            except KeyError:
                self.topWindow.reportError()
                self.topWindow.setStatus('ERROR: Probably unknown column name. Skipping {0} channel for id {1}.'.format(channel, id), color='error')
                self.topWindow.setStatus('Try searching for mistakes, typos and inconsistent naming schemes in your data.', color='error')





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
        #
        # ??
        # tools=, tooltips=
        # figure.line(, line_color="#FF0000", line_width=8, alpha=0.7, legend="PDF")
        # figure.legend.location='center_right'
        # figure.legend.background_fill_color='darkgrey'
        pass




    #TODO refactor all plot types to viz/methods
    #  это позволит и видоизменять язык надписей без труда, и цвета
    #TODO export plot data to standard format
    #TODO bokeh html interactive output, or PLOTLY
    def ANOVA_stats(self, multiData:object, pivotData:object, dataExporter:object)->None:
        """Analysis of variance on distribution data.

        Combinations to include in cross-table must be specified.

        :param multiData: multiData struct with different data channels, unpivoted and ungrouped.
        :param pivotData: ??needed?   pivoted data, mainly after running 'Batch and pivot'.
        :param dataExporter:
        :return:
        """
        self.topWindow.setStatus('ANOVA requested.')
        data=multiData.getChannelById('manu', 'all')
        data['mGesture'].replace(to_replace='^.*(mGe)\d+$', value='\\1', regex=True, inplace=True)
        #self.topWindow.setStatus('Standardizing to z-scores.')
        #проверить есть ли разница в величине f-теста с и без z-score
        #zdata1=scipy.stats.zscore(data1, axis=0)

        ids = ['C', 'N', 'R']
        labels=['Commenter','Narrator','Reteller']
        grouped = data.groupby(['Id', 'mGesture'])['Duration']
        groupedList = [list(grouped)[0][1], list(grouped)[1][1], list(grouped)[2][1]]
        groupedDataframe=DataFrame({'C':groupedList[0],'N':groupedList[1],'R':groupedList[2]})


        #FIXME grid должен быть только по y
        #plt.title('Распределение длительности жестов')
        plt.title('Gesture duration boxplot')
        #plt.xlabel('Роль участника')
        plt.xlabel('Subject role')
        #plt.ylabel('Длительность (с)')
        plt.ylabel('Duration (s)')
        plt.boxplot(groupedList, widths=0.25, showfliers=True, labels=labels)
        # sns.boxplot(data=, hue='Id')
        plt.minorticks_off()
        #можно добавить субграфик просто медиан с доверительными интервалами
        

        #TODO add correlation tests
        #TODO add regression models
        # sns.jointplot()
        # sns.jointplot(, kind='hex')
        # sns.jointplot(, kind='kde')
        # plt.scatter()
        # plt.errorbar()
        
        #что-то типа heatmap
        #f, ax = plt.subplots(figsize=(6, 6))
        #cmap = sns.cubehelix_palette(as_cmap=True, dark=0, light=1, reverse=True)
        #sns.kdeplot(df.x, df.y, cmap=cmap, n_levels=60, shade=True);



        #plt.title('Плотность распределения длительности жестов (гистограмма)')
        plt.title('Gesture duration histogram')
        #plt.xlabel('Длительность (с)')
        plt.xlabel('Duration (s)')
        #plt.ylabel('Плотность')
        plt.ylabel('Density')
        plt.hist(groupedList[0], density=True, cumulative=False, orientation='vertical', rwidth=0.5)

        #plt.bar()
        #with sns.axes_style('darkgrid'):
        #    sns.barplot(, estimator=sum, hue='')
        #scipy.stats.binned_statistic(, statistic='count', bins=10)
        #scipy.stats.cumfreq(, numbins=10)

        #number of modes ??function
        #проверка сбалансированности измерений
        plt.figure(figsize=(6, 2))
        sns.kdeplot(groupedList[0], bw=0.15, shade=False, vertical=False, gridsize=100, cumulative=False, label=labels[0])
        sns.kdeplot(groupedList[1], bw=0.15, shade=False, vertical=False, gridsize=100, cumulative=False, label=labels[1])
        sns.kdeplot(groupedList[2], bw=0.15, shade=False, vertical=False, gridsize=100, cumulative=False, label=labels[2])
        # palette=Greens_d, Blues_d, pastel, Set3
        # sns.violinplot(data=, hue='Id', bw=0.15, split=True, palette='Set3')	#inner='stick'
        # sns.swarmplot(data=, color='w', alpha=0.5)
        plt.title('Gesture duration swarmplot')
        plt.xlabel('Subject role')
        plt.ylabel('Duration (s)')
        sns.swarmplot(data=groupedDataframe)
        plt.minorticks_off()


        #FIXME рефактор чтобы не было копий этого блока
        #FIXME all ylim must be same
        #plt.figure(figsize=(18, 6))
        plt.suptitle('Density function of gesture duration')
        plt.subplot(131)
        subjectNum=0
        #plt.title('Плотность распределения жестов')
        plt.title(labels[subjectNum])
        #plt.xlabel('Длительность (с)')
        plt.xlabel('Duration (s)')
        #plt.ylabel('Плотность, накопленная плотность')
        plt.ylabel('Density, cumulative density')
        #kernel0=scipy.stats.gaussian_kde(groupedList[subjectNum], bw_method='scott')
        loc, scale = scipy.stats.norm.fit(groupedList[subjectNum])
        norm0=scipy.stats.norm(loc=loc, scale=scale)
        xs=numpy.linspace(min(groupedList[subjectNum]),max(groupedList[subjectNum]),100)
        #plt.plot(xs,kernel0(xs))
        sns.distplot(groupedList[subjectNum], kde=True, hist=True, rug=True, vertical=False, label='PDF')
        sns.kdeplot(groupedList[subjectNum], cumulative=True, label='CDF')
        plt.plot(xs, plt.ylim()[1]*norm0.pdf(xs), label='normal')
        plt.legend()
        #
        plt.subplot(132)
        subjectNum = 1
        plt.title(labels[subjectNum])
        plt.xlabel('Duration (s)')
        plt.ylabel('')
        loc, scale = scipy.stats.norm.fit(groupedList[subjectNum])
        norm1 = scipy.stats.norm(loc=loc, scale=scale)
        xs = numpy.linspace(min(groupedList[subjectNum]), max(groupedList[subjectNum]), 100)
        sns.distplot(groupedList[subjectNum], kde=True, hist=True, rug=True, vertical=False, label='PDF')
        sns.kdeplot(groupedList[subjectNum], cumulative=True, label='CDF')
        plt.plot(xs, plt.ylim()[1] * norm1.pdf(xs), label='normal')
        plt.legend()
        #
        plt.subplot(133)
        subjectNum = 2
        plt.title(labels[subjectNum])
        plt.xlabel('Duration (s)')
        plt.ylabel('')
        loc, scale = scipy.stats.norm.fit(groupedList[subjectNum])
        norm2 = scipy.stats.norm(loc=loc, scale=scale)
        xs = numpy.linspace(min(groupedList[subjectNum]), max(groupedList[subjectNum]), 100)
        sns.distplot(groupedList[subjectNum], kde=True, hist=True, rug=True, vertical=False, label='PDF')
        sns.kdeplot(groupedList[subjectNum], cumulative=True, label='CDF')
        plt.plot(xs, plt.ylim()[1] * norm2.pdf(xs), label='normal')
        plt.legend()


        #
        #scipy.stats.norm.rvs(size=100)
        # Q-Q plot можно для разных переменных, чтобы видеть профиль и сравнивать
        # sns.pairplot()
        # g = sns.PairGrid(iris)
        # g.map_diag(sns.kdeplot)
        # g.map_offdiag(sns.kdeplot, cmap="Blues_d", n_levels=6);
        scipy.stats.kstest(groupedList[0], norm0.cdf)
        scipy.stats.kstest(groupedList[1], norm1.cdf)
        scipy.stats.kstest(groupedList[2], norm2.cdf)
        scipy.stats.levene(groupedList[0],groupedList[1],groupedList[2])
        scipy.stats.levene(groupedList[0],groupedList[2])
        scipy.stats.levene(groupedList[1],groupedList[2])


        self.topWindow.setStatus('Sample size is:')
        #statsmodels.stats.power.FTestAnovaPower.power
        self.topWindow.setStatus('F-test:')
        scipy.stats.f_oneway(groupedList[0],groupedList[1])
        #scipy.stats.f_oneway(groupedList[0],groupedList[2])
        #scipy.stats.f_oneway(groupedList[1],groupedList[2])


        scipy.stats.kruskal(groupedList[0],groupedList[1],groupedList[2])
        scipy.stats.mannwhitneyu(groupedList[1],groupedList[2])


        #effect size
        #scheffe test

        plt.savefig('img/{0}_Figure.png'.format(datetime.now().strftime('%Y-%m-%d %H_%M_%S')))




    def manuVocTempoStats(self, multiData: object, dataExporter: object) -> None:
        """Different statistics for special preprocessed 'manu-voc-tempo' data type.

        :param multiData:
        :param dataExporter:
        :return:
        """
        self.topWindow.setStatus('Special statistics: manu-voc-tempo requested.')
        data = multiData.getChannelById('manu-voc-tempo', 'all')
        dataEDU=data.loc[data['EventType']=='EDU']
        dataFRG=data.loc[data['EventType']=='FRG']

        EDUgrouped = dataEDU.groupby(['Interval', 'Id'])['Tempo']
        EDUgroupedN = [list(EDUgrouped)[1][1], list(EDUgrouped)[4][1]]
        EDUgroupedR = [list(EDUgrouped)[5][1], list(EDUgrouped)[6][1]]
        #
        FRGgrouped = dataFRG.groupby(['Interval', 'Id'])['Tempo']
        FRGgroupedN = [list(FRGgrouped)[1][1], list(FRGgrouped)[4][1]]
        FRGgroupedR = [list(FRGgrouped)[5][1], list(FRGgrouped)[6][1]]

        plt.subplot(221)
        plt.title('Narrator\nEDU')
        plt.axis(ymin=-50,ymax=1500)
        plt.ylabel('Tempo')
        bplot1 = plt.boxplot(EDUgroupedN, widths=0.25, showfliers=True, labels=['',''])
        plt.suptitle('TEMPO BOXPLOT')
        plt.grid(True)
        #
        plt.subplot(222)
        plt.title('Reteller\nEDU')
        plt.axis(ymin=-50, ymax=1500)
        bplot2 = plt.boxplot(EDUgroupedR, widths=0.25, showfliers=True, labels=['',''])
        #
        plt.subplot(223)
        plt.title('FRG')
        plt.axis(ymin=-50, ymax=1500)
        plt.xlabel('Interval')
        plt.ylabel('Tempo')
        bplot3 = plt.boxplot(FRGgroupedN, widths=0.25, showfliers=True, labels=['Telling', 'Conversation'])
        #
        plt.subplot(224)
        plt.title('FRG')
        plt.axis(ymin=-50, ymax=1500)
        plt.xlabel('Interval')
        bplot4 = plt.boxplot(FRGgroupedR, widths=0.25, showfliers=True, labels=['Conversation', 'Retelling'])
        #
        colors = ['green','blue','blue','red','green','blue','blue','red']
        colInd=0
        for bplot in (bplot1, bplot2, bplot3, bplot4):
            for patch in bplot['boxes']:
                patch.set_facecolor(colors[colInd])
                colInd = colInd+1


        trace0 = go.Box(y=groupedList[0], name='Telling')
        trace1 = go.Box(y=groupedList[1], name='Conversation')
        layout = dict(title='VOCAL TEMPO BOXPLOT, NARRATOR',
                      xaxis=dict(title='Interval'),
                      yaxis=dict(title='Tempo'))
        figData = [trace0, trace1]
        fig = dict(data=figData, layout=layout)
        py.plot(fig, filename='boxplot01.html', auto_open=True)



        plt.suptitle('VOCAL TEMPO PDF')
        plt.subplot(221)
        plt.title('Narrator\nEDU')
        plt.axis(xmax=1200,ymax=0.0040)
        plt.ylabel('Probability')
        sns.kdeplot(EDUgroupedN[0], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Telling', color='green')
        sns.kdeplot(EDUgroupedN[1], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Conversation', color='blue')
        plt.subplot(222)
        plt.title('Reteller\nEDU')
        plt.axis(xmax=1200,ymax=0.0040)
        sns.kdeplot(EDUgroupedR[0], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Conversation', color='blue')
        sns.kdeplot(EDUgroupedR[1], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Retelling', color='red')
        #
        plt.subplot(223)
        plt.title('FRG')
        plt.axis(xmax=1200,ymax=0.0040)
        plt.xlabel('Tempo')
        plt.ylabel('Probability')
        sns.kdeplot(FRGgroupedN[0], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Telling', color='green')
        sns.kdeplot(FRGgroupedN[1], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Conversation', color='blue')
        plt.subplot(224)
        plt.title('FRG')
        plt.axis(xmax=1200,ymax=0.0040)
        plt.xlabel('Tempo')
        sns.kdeplot(FRGgroupedR[0], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Conversation', color='blue')
        sns.kdeplot(FRGgroupedR[1], bw=10, shade=True, vertical=False, gridsize=100, cumulative=False, label='Retelling', color='red')









    #TODO add ratio by index column to all groupings where id or id 2 present
    #FIXME interval sort order must be always unsorted
    #TODO must refactor all describe, grouping and filtering logic to separate method in multidata class (incapsulation)
    #TODO can factor out returned dataframes from multidata to special inherited and extended class, e.g. DataChannel
    #  который будет иметь hooks на методы обсчета статистики и возвращать нужные groupedby таблицы
    #  это позволит делать method chaining через точку
    def groupbyListAndDescribe(self, data:object, groupby:object, on:object) -> DataFrame:
        """Slices data on groupby, aggregates on column and adds some descriptive columns.

        :param data: Dataframe to slice.
        :param groupby: List of columns or str to groupby, can be empty.
        :param on: Columns to aggregate on.
        :return: data slice.
        """
        #TODO лучше всего вычислять метрики постолбцово, и потом просто join их всех - тогда нет мороки с сортировкой столбцов
        self.topWindow.logger.debug('group by list and describe')
        #data.fillna('<NA>',inplace=True)
        if type(groupby) is str:
            groupby=[groupby]
        if type(on) is str:
            on=[on]

        if len(groupby)==0:
            onned=data[on]
            agg1 = onned.agg(['count', 'sum', 'mean', 'std', 'min'])
            agg2 = onned.agg('quantile', q=[0.25, 0.5, 0.75])
            agg3 = onned.agg(['max'])
            sliced = pandas.concat([agg1, agg2, agg3])
            sliced=DataFrame(sliced).transpose()
            #recordDur=self.settingsReader.totalDuration()
            recordDur = numpy.sum([Utils.parseTime(t) for t in data['Interval duration'].unique()])
            sliced.insert(0, 'interval duration sum', value=recordDur.total_seconds())
        else:
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
            #TODO FIXME что если уровень только 1
            #2018.11.12 с учетом мультииндекса в столбцах
            sliced = sliced.reorder_levels([1,0], axis=1)
            sliced = sliced.reindex(labels=['count', 'sum', 'mean', 'std', 'min', 0.25, 0.5, 0.75, 'max'],
                                    axis=1, level=0)
            sliced = sliced.reindex(labels=on, axis=1, level=1)
            #sliced.sort_index(axis=1, level=0, inplace=True, sort_remaining=False)
            #FIXME что если уровень 1
            slicedCountRat = pandas.concat([sliced['count'] / sliced['count'].sum()], keys=['count ratio'], axis=1)
            slicedSumRat = pandas.concat([sliced['sum'] / sliced['sum'].sum()], keys=['sum ratio'], axis=1)
            #sliced.insert(1, 'count ratio', value=slicedCountRat)
            #sliced.insert(3, 'sum ratio', value=slicedSumRat)
            sliced = sliced.join(slicedCountRat)
            sliced = sliced.join(slicedSumRat)
            #теперь сортируем
            sliced = sliced.reindex(labels=['count', 'count ratio', 'sum', 'sum ratio', 'mean', 'std', 'min', 0.25, 0.5, 0.75, 'max'],
                                    axis=1, level=0)
            sliced = sliced.reindex(labels=on, axis=1, level=1)
            # считаем ratio от длительности интервала
            if ('Interval' in groupby) and (len(groupby) == 1):
                #recordDur = self.settingsReader.totalDuration()
                #for 'channels_appended' dataframes
                recordDur = numpy.sum([Utils.parseTime(t) for row in grouped['Interval duration'].unique() for t in row]).total_seconds()
                #не все интервалы могут присутствовать в срезе
                durs=[]
                #FIXME hotfix
                durs = [[Utils.parseTime(t) for t in row] for row in grouped['Interval duration'].unique()]
                durs = [numpy.sum(parsed) for parsed in durs]
                #for interval in list(sliced.index):
                #    durs.append(self.settingsReader.getDurationById(interval))
                durs=pandas.concat([Series(durs)/numpy.timedelta64(1,'s')], keys=['interval duration'], axis=1)
                durs.index = sliced.index
                dursDivided = pandas.concat([durs/recordDur], keys=['interval duration ratio'], axis=1)
                slicedSumRatByDur = pandas.concat([sliced['sum'] / durs], keys=['sum ratio by interval'], axis=1)
                #sliced.insert(0, 'interval duration', value=durs)
                #FIXME need formatting index
                #sliced = sliced.join(durs)
                #sliced.insert(1, 'interval duration ratio', value=durs/recordDur)#.total_seconds())
                #sliced = sliced.join(dursDivided)
                #sliced.insert(6, 'sum ratio by interval', value=slicedSumRatByDur)
                #sliced = sliced.join(slicedSumRatByDur)
                sliced = sliced.reindex(labels=['count', 'count ratio', 'sum', 'sum ratio', 'mean', 'std', 'min', 0.25, 0.5, 0.75, 'max'],
                                        axis=1, level=0)
                sliced = sliced.reindex(labels=on, axis=1, level=1)
            #считаем ratio по интервалам
            elif ('Interval' in groupby or 'Id' in groupby or 'Id 2' in groupby) and (len(groupby)>1):
                #2018.11.11 берем первую найденную категориальную переменную из заданного списка
                #TODO можно добавить и другие, например, EDU, и можно сделать расчет ratio сразу по всем таким словам в каждой таблице
                for word in ['Interval','Id','Id 2']:
                    if word in groupby:
                        break
                #2018.11.12 not needed?
                ints=sliced.index.get_level_values(word).tolist()   #[int for int, *level in list(sliced.index)]
                #slicedCountRatByInt=pandas.concat([sliced['count'] / list(sliced['count'].groupby(word).sum()[ints])], keys=['count ratio by {0}'.format(word.lower())], axis=1)
                colName1='count ratio by {0}'.format(word.lower())
                slicedCountRatByInt=pandas.concat([sliced['count'] / sliced['count'].groupby(word).sum()], keys=[colName1], axis=1)
                #slicedSumRatByInt = pandas.concat([sliced['sum'] / list(sliced['sum'].groupby(word).sum()[ints])], keys=['sum ratio by {0}'.format(word.lower())], axis=1)
                colName2='sum ratio by {0}'.format(word.lower())
                slicedSumRatByInt = pandas.concat([sliced['sum'] / sliced['sum'].groupby(word).sum()], keys=[colName2], axis=1)
                #sliced.insert(2, 'count ratio by {0}'.format(word.lower()), value=slicedCountRatByInt)
                sliced = sliced.join(slicedCountRatByInt)
                #sliced.insert(5, 'sum ratio by {0}'.format(word.lower()), value=slicedSumRatByInt)
                sliced = sliced.join(slicedSumRatByInt)
                sliced = sliced.reindex(labels=['count', 'count ratio', colName1, 'sum', 'sum ratio', colName2, 'mean', 'std', 'min', 0.25, 0.5, 0.75, 'max'],
                                        axis=1, level=0)
                sliced = sliced.reindex(labels=on, axis=1, level=1)


        # вносим описание таблицы
        #self.groupedByNum = self.groupedByNum+1
        sliced.description={'groupby':groupby, 'on':on} #'num':self.groupedByNum
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
            self.topWindow.setStatus('ERROR: Number of sheets specified does not match the data sequence.')
            raise ValueError

        writer=pandas.ExcelWriter(file)
        dfNum=0
        dfNums={}
        startrow=1
        startrows={}
        for sheet in sheets:
            dfNums[sheet]=0
            startrows[sheet]=1

        for df in data:
            #st = Styler(df, precision=3)
            #st.background_gradient()
            #st.highlight_max()
            #st.highlight_min()
            #st.highlight_null()

            if len(df.description['groupby']):
                groupedByText = ', grouped by {0}'.format(str(df.description['groupby']).replace('[', '').replace(']', '').replace("'", ''))
                rowDelta=5
            else:
                groupedByText = ''
                rowDelta=3

            if len(sheets):
                startrow=startrows[sheets[dfNum]]

                df.to_excel(writer, startrow=startrow, sheet_name=sheets[dfNum])
                workSheet = writer.sheets[sheets[dfNum]]
                #workSheet.write(startrow-1, 0, 'Table {0}. {1}{2}'.format(dfNum+1, df.description['on'], groupedByText))
                workSheet.write(startrow-1, 0, 'Table {0}({1})'.format(dfNums[sheets[dfNum]]+1, dfNum+1))
                #st.to_excel(writer, startrow=startrow, sheet_name=sheets[dfNum])
                dfNums[sheets[dfNum]] = dfNums[sheets[dfNum]]+1
                startrows[sheets[dfNum]]=startrow + df.shape[0] + rowDelta
            else:
                if len(df):
                    self.topWindow.logger.debug('writing xls file')
                    df.to_excel(writer, startrow=startrow)
                    workSheet = writer.sheets['Sheet1']
                    #workSheet.write(startrow - 1, 0, 'Table {0}. {1}{2}'.format(dfNum+1, df.description['on'], groupedByText))
                    workSheet.write(startrow - 1, 0, 'Table {0}'.format(dfNum+1))
                    #st.to_excel(writer, startrow=startrow)
                    startrow = startrow + df.shape[0] + rowDelta
                else:
                    self.topWindow.setStatus('WARNING: Empty table encountered in file {0}. Omitting from report.'.format(os.path.basename(file)))
            dfNum = dfNum + 1

            writer.save()