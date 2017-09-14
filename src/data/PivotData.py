import os
import re


import numpy
import pandas



class PivotData:

    """Class to hold pivoted tables."""

    def __init__(self,topWindow:object):
        self.topWindow = topWindow

        self.tabDict={}
        self.pivots={}



    def pivot(self,settingsReader:object,stats:object)->None:
        """Makes pivot tables, writes to disk and keeps them in this class.
        
        :param settingsReader: object with settings.
        :param stats: Stats object to write files with.
        :return: 
        """

        # listing tables
        types = settingsReader.unique('file', 'type', serial=True)
        ids = settingsReader.unique('file', 'id', serial=True)
        tabDict = {}
        for type in types:
            if type == 'ey':
                continue
            tabDict[type] = {}
            for id in ids:
                files = settingsReader.getTypeById(type, id, serial=True)
                if len(files):
                    tabDict[type][id] = {}
                for fIter in range(len(files)):
                    file = files[fIter]
                    batchNum = file.get('batchNum')
                    dataDir = settingsReader.batchDir + '/' + batchNum
                    # добавляем имя файла чтобы использовать как dataframe index
                    pathAttr = os.path.splitext(file.get('path'))[0]
                    dataFile = dataDir + '/' + pathAttr + '_report'

                    # iterating through possible tables
                    tabNum = 1
                    tabFile = dataFile + '_' + str(tabNum) + '.csv'
                    tabDict[type][id][batchNum] = {}
                    tabDict[type][id][batchNum]['pathAttr'] = pathAttr
                    while os.path.exists(tabFile):
                        # reading table
                        table = pandas.read_csv(tabFile, sep='\t', index_col=0, encoding='UTF-8')
                        # dividing index columns from data columns
                        r = re.compile('float64')
                        tNum = 0
                        for t in table.dtypes.astype(str).tolist():
                            if r.search(t):
                                break
                            tNum = tNum + 1
                        newIndex = list(table.columns[0:tNum])
                        newIndex.insert(0, table.index)
                        table.set_index(newIndex, inplace=True)
                        tabDict[type][id][batchNum][tabNum] = table

                        tabNum = tabNum + 1
                        tabFile = dataFile + '_' + str(tabNum) + '.csv'

        self.tabDict=tabDict
        pivots={}

        # combining tables
        self.topWindow.setStatus('Pivoting...')
        for type in tabDict.keys():
            tabs = []
            csvs = []
            iKeys = list(tabDict[type].keys())
            bKeys = list(tabDict[type][list(iKeys)[0]].keys())
            # учитываем наличие атрибутов
            for tabNum in range(len(tabDict[type][list(iKeys)[0]][list(bKeys)[0]]) - 1):
                toCombine = [tabDict[type][i][b][tabNum + 1] for i in iKeys for b in bKeys]
                pathAttrs = [tabDict[type][i][b]['pathAttr'] for i in iKeys for b in bKeys]
                labels1 = numpy.concatenate([[iKey] * len(bKeys) for iKey in range(len(iKeys))])
                labels2 = [int(bKey) - 1 for bKey in bKeys] * len(iKeys)
                mi = pandas.MultiIndex(levels=[iKeys, pathAttrs], labels=[labels1, range(len(pathAttrs))])
                mi2 = pandas.MultiIndex(levels=[iKeys, bKeys], labels=[labels1, labels2])
                tabs.append(pandas.concat(toCombine, keys=mi, names=['Id', 'Record tag'], copy=False))
                csvs.append(pandas.concat(toCombine, keys=mi2, names=['Id', 'Record tag'], copy=False))

            # storing tables for further statistic
            pivots[type]=csvs

            # writing to file
            file = settingsReader.batchDir + '/' + type + '_pivot.xls'
            if type == 'gaze':
                # FIXME sheets list from global enum
                sheets = ['Fixations', 'Fixations', 'Saccades', 'Saccades', 'EyesNotFounds', 'EyesNotFounds']
            else:
                sheets = []
            stats.saveIncrementally(file, tabs, sheets=sheets)
            #stats.saveCSV(file, csvs)


        #storing all data to class
        self.pivots=pivots