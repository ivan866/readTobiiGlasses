import numpy
import pandas



#указать путь к файлам с экспортированными данными
workPath='G:/text/org/ИЯ РАН/exportData'
participantIds=['Project1 Data Export_02']


workDirs=workPath
gazeDataFiles=[workDirs+'/'+participantId+'.tsv' for participantId in participantIds]

cameraWidthPx=1920
cameraHeightPx=1080



#считываем данные
gazeData=pandas.read_csv(gazeDataFiles[0],sep="\t",decimal=",",encoding='UTF-16',
#==============================================================================
#numpy не поддерживает столбцы типа integer в которых есть NA
#                          dtype={'Recording timestamp':numpy.float32, 
#                                 'Gaze point X':numpy.float16, 'Gaze point Y':numpy.float16, 
#                                 'Pupil diameter left':numpy.float32, 'Pupil diameter right':numpy.float32, 
#                                 'Eye movement type':numpy.str, 'Gaze event duration':numpy.float16, 'Eye movement type index':numpy.float16, 
#                                 'Fixation point X':numpy.float16, 'Fixation point Y':numpy.float16},
#==============================================================================
                         usecols=['Recording timestamp', 
                                  'Gaze point X', 'Gaze point Y', 
                                  'Pupil diameter left', 'Pupil diameter right', 
                                  'Eye movement type', 'Gaze event duration', 'Eye movement type index', 
                                  'Fixation point X', 'Fixation point Y'])
#переводим в секунды
gazeData['Recording timestamp']/=1000
gazeData['Gaze event duration']/=1000
#оставляем достаточную точность
#gazeData=gazeData.round(6)


#вырезаем строки с фиксациями
fixations=gazeData.loc[gazeData['Eye movement type']=='Fixation'][['Recording timestamp',
                                                                   'Gaze event duration','Eye movement type index',
                                                                   'Fixation point X','Fixation point Y']]
#удаляем одинаковые строки, но без учета первого столбца
fixations.drop_duplicates(fixations.columns[range(1,fixations.shape[1])],inplace=True)

#теперь саккады
def calcSaccadeGazePoints(row):
     prevPosInd=int(numpy.where(gazeData['Recording timestamp']==row['Recording timestamp'])[0])-1
     if prevPosInd:
         prevX=gazeData.iloc[prevPosInd]['Gaze point X']
         prevY=gazeData.iloc[prevPosInd]['Gaze point Y']
         row['Start gaze point X']=prevX
         row['Start gaze point Y']=prevY
    
     nextPosInd=0
     try:
         nextPosInd=int(numpy.where(gazeData['Recording timestamp']==(row['Recording timestamp']+row['Gaze event duration']).round(6))[0])
     except TypeError:
         print('Cannot find next position')
     if nextPosInd:
         nextX=gazeData.iloc[nextPosInd]['Gaze point X']
         nextY=gazeData.iloc[nextPosInd]['Gaze point Y']
         row['End gaze point X']=nextX
         row['End gaze point Y']=nextY
         
     return row
   
saccades=gazeData.loc[gazeData['Eye movement type']=='Saccade'][['Recording timestamp',
                                                                 'Gaze event duration','Eye movement type index']]
saccades.drop_duplicates(saccades.columns[range(1,saccades.shape[1])],inplace=True)
saccades=saccades.apply(calcSaccadeGazePoints,axis=1)


#участки потерянного контакта
eyesNotFounds=gazeData.loc[gazeData['Eye movement type']=='EyesNotFound'][['Recording timestamp',
                                                                           'Gaze event duration','Eye movement type index']]
eyesNotFounds.drop_duplicates(eyesNotFounds.columns[range(1,eyesNotFounds.shape[1])],inplace=True)

#неизвестные события
unclassifieds=gazeData.loc[gazeData['Eye movement type']=='Unclassified'][['Recording timestamp',
                                                                           'Gaze point X','Gaze point Y',
                                                                           'Gaze event duration','Eye movement type index']]
unclassifieds.drop_duplicates(unclassifieds.columns[range(1,unclassifieds.shape[1])],inplace=True)


#события в основных данных больше не нужны
gazeData.drop(['Eye movement type','Gaze event duration','Eye movement type index','Fixation point X','Fixation point Y'],axis=1,inplace=True)

    

