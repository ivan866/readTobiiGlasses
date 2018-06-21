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




    #TODO modernize method to use generator methods from settingsReader and multiData
    #TODO currently pivots only desc-stats report files
    def pivot(self, settingsReader:object, stats:object)->None:
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
            #?? media types not applicable
            if type == 'vi' or type== 'ey' or type== 'eyf' or type== 'au':
                continue
            tabDict[type] = {}
            for id in ids:
                files = settingsReader.getTypeById(type, id, serial=True)
                if len(files):
                    tabDict[type][id] = {}
                for fIter, file in enumerate(files):
                    batchNum = file.get('batchNum')
                    dataDir = '{0}/{1}'.format(settingsReader.batchDir, batchNum)
                    # добавляем имя файла чтобы использовать как dataframe index
                    pathAttr = os.path.splitext(file.get('path'))[0]
                    #FIXME suffix hard-coded and !duplicated (stats have also)
                    dataFile = '{0}/{1}_descriptive'.format(dataDir, pathAttr)

                    # iterating through possible tables
                    tabNum = 1
                    tabFile = '{0}_{1}.csv'.format(dataFile, tabNum)
                    tabDict[type][id][batchNum] = {}
                    tabDict[type][id][batchNum]['pathAttr'] = pathAttr
                    #collecting all report tables to single multilevel dict struct
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
                        tabFile = '{0}_{1}.csv'.format(dataFile, tabNum)



        #struct ready
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
            #try:
            for tabNum in range(len(tabDict[type][list(iKeys)[0]][list(bKeys)[0]]) - 1):
                toCombine = [tabDict[type][i][b][tabNum + 1] for i in iKeys for b in bKeys]
                pathAttrs = [tabDict[type][i][b]['pathAttr'] for i in iKeys for b in bKeys]
                labels1 = numpy.concatenate([[iKey] * len(bKeys) for iKey in range(len(iKeys))])
                labels2 = [int(bKey) - 1 for bKey in bKeys] * len(iKeys)
                mi = pandas.MultiIndex(levels=[iKeys, pathAttrs], labels=[labels1, range(len(pathAttrs))])
                mi2 = pandas.MultiIndex(levels=[iKeys, bKeys], labels=[labels1, labels2])
                tabs.append(pandas.concat(toCombine, keys=mi, names=['Id', 'Record tag'], copy=False))
                csvs.append(pandas.concat(toCombine, keys=mi2, names=['Id', 'Record tag'], copy=False))
            #except:
            #    self.topWindow.reportError()
            #    self.topWindow.setStatus('ERROR: Failed appending pivot tables. Do you have lonely annotation of type {0} in batch packet?'.format(type))
            #    self.topWindow.setStatus('WARNING: Annotation type can possibly be absent in batch result.', color='error')

            # storing tables for further statistic
            pivots[type]=csvs



            #FIXME need move this block to more appropriate place, need abstract this procedure
            # writing to file
            file = '{0}/{1}_pivot.xls'.format(settingsReader.batchDir, type)
            if type == 'gaze':
                # FIXME sheets list from global enum
                sheets = ['Fixations', 'Fixations', 'Saccades', 'Saccades', 'EyesNotFounds', 'EyesNotFounds']
            else:
                sheets = []
            self.topWindow.logger.debug('pivoted, save incrementally')
            stats.saveIncrementally(file, tabs, sheets=sheets)
            #stats.saveCSV(file, csvs)


        #storing all data to class
        self.pivots=pivots