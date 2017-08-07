import os
import argparse
import datetime
import subprocess
import re

from tkinter import *
from tkinter import filedialog

import xml.etree.ElementTree as ET

import numpy
import pandas




dataDir=''
settingsFile=''
def selectSettings(file=''):
    global dataDir
    global settingsFile
    if not file:
        settingsFile = filedialog.askopenfilename(filetypes = (("eXtensible Markup Language","*.xml"),("all files","*.*")))
    else:
        settingsFile=file
    dataDir=os.path.dirname(settingsFile)
    status.config(text='Settings file selected (not read or modified yet).')
    
    
def openSettings():
    status.config(text='Calling external editor...')
    root.update_idletasks()
    subprocess.run('npp/notepad++.exe '+settingsFile)
    status.config(text='Returned from external editor.')



#считываем данные
settingsTree=''
settings=''
data={}
def readData():
    global settingsTree
    global settings
    global data
    settingsTree=ET.parse(settingsFile)
    settings=settingsTree.getroot()
    status.config(text='Settings parsed.')
    
    data['availColumns']=[]
    data['gaze']=[]
    data['fixations']=[]
    data['saccades']=[]
    data['eyesNotFounds']=[]
    data['unclassifieds']=[]
    data['gyro']=[]
    data['accel']=[]
    for file in settings.findall("file[@type='gaze']"):
        gazeFile=dataDir+'/'+file.get('path')
        status.config(text='Reading gaze data (file '+os.path.basename(gazeFile)+')...')
        root.update_idletasks()
        #узнаем какие столбцы присутствуют
        headers=pandas.read_csv(gazeFile,sep="\t",nrows=1,encoding='UTF-16')
        availColumns=[i for i in list(headers.columns) if re.match('Recording timestamp|Gaze point|Gaze direction|Pupil diameter|Eye movement type|Gaze event duration|Fixation point|Gyro|Accelerometer',i)]
        data['availColumns'].append(availColumns)
        gazeData=pandas.read_csv(gazeFile,sep="\t",decimal=",",encoding='UTF-16',
        #==============================================================================
        #numpy не поддерживает столбцы типа integer в которых есть NA
        #                          dtype={'Recording timestamp':numpy.float32, 
        #                                 'Gaze point X':numpy.float16, 'Gaze point Y':numpy.float16, 
        #                                 'Pupil diameter left':numpy.float32, 'Pupil diameter right':numpy.float32, 
        #                                 'Eye movement type':numpy.str, 'Gaze event duration':numpy.float16, 'Eye movement type index':numpy.float16, 
        #                                 'Fixation point X':numpy.float16, 'Fixation point Y':numpy.float16},
        #==============================================================================
                                 usecols=availColumns)
        #переводим в секунды
        gazeData['Recording timestamp']/=1000
        gazeData['Gaze event duration']/=1000
        #оставляем достаточную точность
        #gazeData=gazeData.round(6)
        
        
        #гироскоп и акселерометр пишутся не синфазно с трекером, вырезаем в отдельные таблицы
        if 'Gyro X' and 'Gyro Y' and 'Gyro Z' and 'Accelerometer X' and 'Accelerometer Y' and 'Accelerometer Z' in availColumns:
            gyro=gazeData[['Recording timestamp',
                           'Gyro X','Gyro Y','Gyro Z']]
            #убираем пустые строки, но без учета столбца времени
            gyro.dropna(subset=(['Gyro X','Gyro Y','Gyro Z']),how='all',inplace=True)
            data['gyro'].append(gyro)
        
            accel=gazeData[['Recording timestamp',
                            'Accelerometer X','Accelerometer Y','Accelerometer Z']]
            accel.dropna(subset=(['Accelerometer X','Accelerometer Y','Accelerometer Z']),how='all',inplace=True)
            data['accel'].append(accel)
        
            #гироскоп в основных данных больше не нужен
            gazeData.drop(['Gyro X','Gyro Y','Gyro Z',
                           'Accelerometer X','Accelerometer Y','Accelerometer Z'],axis=1,inplace=True)
            #убираем пустые строки
            gazeData=gazeData[(gazeData['Gaze point X'].notnull()) & (gazeData['Gaze point Y'].notnull()) | \
                              (gazeData['Eye movement type']=='EyesNotFound')]
        else:
            #no sparse lists in python stdlib, filling with zeros
            data['gyro'].append(0)
            data['accel'].append(0)
        
        
        if 'Eye movement type' in availColumns:
            #вырезаем строки с фиксациями
            fixations=gazeData.loc[gazeData['Eye movement type']=='Fixation'][['Recording timestamp',
                                                                               'Gaze event duration','Eye movement type index',
                                                                               'Fixation point X','Fixation point Y']]
            #удаляем одинаковые строки, но без учета первого столбца
            fixations.drop_duplicates(fixations.columns[range(1,fixations.shape[1])],inplace=True)
            timeReadable=pandas.to_datetime(fixations['Recording timestamp'],unit='s')
            fixations.insert(1,'Timecode',timeReadable.dt.strftime('%M:%S.%f'))
            data['fixations'].append(fixations)
        
        
            #теперь саккады
            def calcSaccadeGazePoints(row):
                prevPosInd=numpy.where(gazeData['Recording timestamp']<row['Recording timestamp'])[0][-1]
                prevX=gazeData.iloc[prevPosInd]['Gaze point X']
                prevY=gazeData.iloc[prevPosInd]['Gaze point Y']
                row['Start gaze point X']=prevX
                row['Start gaze point Y']=prevY
               
                nextPosInd=numpy.where(gazeData['Recording timestamp']>=((row['Recording timestamp']+row['Gaze event duration']).round(6)))[0][0]
                nextX=gazeData.iloc[nextPosInd]['Gaze point X']
                nextY=gazeData.iloc[nextPosInd]['Gaze point Y']
                row['End gaze point X']=nextX
                row['End gaze point Y']=nextY
                    
                return row
               
            saccades=gazeData.loc[gazeData['Eye movement type']=='Saccade'][['Recording timestamp',
                                                                             'Gaze event duration','Eye movement type index']]
            saccades.drop_duplicates(saccades.columns[range(1,saccades.shape[1])],inplace=True)
            status.config(text='Parsing saccades (file '+os.path.basename(gazeFile)+')...')
            root.update_idletasks()
            saccades=saccades.apply(calcSaccadeGazePoints,axis=1)
            saccades=saccades[['Recording timestamp',
                               'Gaze event duration','Eye movement type index',
                               'Start gaze point X','Start gaze point Y',
                               'End gaze point X','End gaze point Y']]
            timeReadable=pandas.to_datetime(saccades['Recording timestamp'],unit='s')
            saccades.insert(1,'Timecode',timeReadable.dt.strftime('%M:%S.%f'))
            data['saccades'].append(saccades)
        
        
            #участки потерянного контакта
            eyesNotFounds=gazeData.loc[gazeData['Eye movement type']=='EyesNotFound'][['Recording timestamp',
                                                                                       'Gaze event duration','Eye movement type index']]
            eyesNotFounds.drop_duplicates(eyesNotFounds.columns[range(1,eyesNotFounds.shape[1])],inplace=True)
            data['eyesNotFounds'].append(eyesNotFounds)
            
            #неизвестные события
            unclassifieds=gazeData.loc[gazeData['Eye movement type']=='Unclassified'][['Recording timestamp',
                                                                                       'Gaze point X','Gaze point Y',
                                                                                       'Gaze event duration','Eye movement type index']]
            unclassifieds.drop_duplicates(unclassifieds.columns[range(1,unclassifieds.shape[1])],inplace=True)
            data['unclassifieds'].append(unclassifieds)
        
        
            #события в основных данных больше не нужны
            gazeData.drop(['Eye movement type','Gaze event duration','Eye movement type index',
                           'Fixation point X','Fixation point Y'],
                            axis=1,inplace=True)
        else:
            data['fixations'].append(0)
            data['saccades'].append(0)
            data['eyesNotFounds'].append(0)
            data['unclassifieds'].append(0)
        
        
        data['gaze'].append(gazeData)
        
    status.config(text='All valueable data read successfully.')




def dataSummary():
    pass

def validateData():
    pass


#сохраняем фиксации и саккады в файл
def extractFixations(format):
    iter=0
    for file in settings.findall("file[@type='gaze']"):
        written=False
        if 'Eye movement type' in data['availColumns'][iter]:
            written=True
            fixFile=os.path.splitext(file.get('path'))[0]+'_Fixations.'+format
            sacFile=os.path.splitext(file.get('path'))[0]+'_Saccades.'+format
            if format=='csv':
                data['fixations'][iter].to_csv(dataDir+'/'+fixFile,sep='\t',index=False)
                data['saccades'][iter].to_csv(dataDir+'/'+sacFile,sep='\t',index=False)
            elif format=='xls':
                data['fixations'][iter].to_excel(dataDir+'/'+fixFile,index=False)
                data['saccades'][iter].to_excel(dataDir+'/'+sacFile,index=False)
        iter=iter+1
    if written:
        status.config(text='Fixations and saccades saved to files.')
    else:
        status.config(text='There is no data to write (id )'+iter+'.')
    
def extractGyro():
    iter=0
    for file in settings.findall("file[@type='gaze']"):
        written=0
        if 'Gyro X' in data['availColumns'][iter] and 'Gyro Y' in data['availColumns'][iter] and 'Gyro Z' in data['availColumns'][iter]:
            written=written+1
            gyroFile=os.path.splitext(file.get('path'))[0]+'_Gyro.csv'
            data['gyro'][iter].to_csv(dataDir+'/'+gyroFile,sep='\t',index=False)
        if 'Accelerometer X' in data['availColumns'][iter] and 'Accelerometer Y' in data['availColumns'][iter] and 'Accelerometer Z' in data['availColumns'][iter]:
            written=written+10
            accelFile=os.path.splitext(file.get('path'))[0]+'_Accelerometer.csv'
            data['accel'][iter].to_csv(dataDir+'/'+accelFile,sep='\t',index=False)
        iter=iter+1
    if written==1:
        status.config(text='Available gyroscope data saved to files.')
    elif written==10:
        status.config(text='Available accelerometer data saved to files.')
    elif written==11:
        status.config(text='Both available gyroscope and accelerometer data saved to files.')
    else:
        status.config(text='There is no sensor data to write (id )'+iter+'.')


#stats
def calcStats():
    pass


def saveStats():
    now=datetime.datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    dateTag=ET.Element('date')
    dateTag.text=now
    settings.append(dateTag)
    
    saveDir=dataDir+'/stats_'+now
    os.mkdir(saveDir)
    settingsTree.write(saveDir+'/'+os.path.basename(settingsFile))
    status.config(text='Statistics saved.')



#viz
videoEyWidthPx=1920
videoEyWidthPx=1080
def tempoPlot():
    pass

def stubPlot():
    status.config(text='Not implemented.')
   



#главное окно
root=Tk()
root.geometry('640x400')
root.title('Read Tobii Glasses')

rootMenu=Menu(root)
root.config(menu=rootMenu)
settingsMenu = Menu(rootMenu,tearoff=0)
settingsMenu.add_command(label="Select...", command=selectSettings)
settingsMenu.add_command(label="Modify in external editor", command=openSettings)
rootMenu.add_cascade(label="Settings",menu=settingsMenu)

dataMenu = Menu(rootMenu,tearoff=0)
dataMenu.add_command(label="Parse settings and read data", command=readData)
dataMenu.add_command(label="Extract fixation lines to CSV", command=lambda: extractFixations('csv'))
dataMenu.add_command(label="Extract fixation lines to Excel", command=lambda: extractFixations('xls'))
dataMenu.add_command(label="Extract gyroscope data to CSV", command=extractGyro)
dataMenu.add_command(label="Validity tests", command=validateData)
dataMenu.add_command(label="Summary", command=dataSummary)
rootMenu.add_cascade(label="Data",menu=dataMenu)

statsMenu = Menu(rootMenu,tearoff=0)
statsMenu.add_command(label="Calculate", command=calcStats)
statsMenu.add_command(label="Save to Excel", command=saveStats)
rootMenu.add_cascade(label="Statistics",menu=statsMenu)

vizMenu = Menu(rootMenu,tearoff=0)
vizMenu.add_command(label="Gaze overlay", command=stubPlot)
vizMenu.add_command(label="3D gaze vectors", command=stubPlot)
vizMenu.add_command(label="Temporal plot", command=tempoPlot)
vizMenu.add_command(label="Spatial plot", command=stubPlot)
vizMenu.add_command(label="Combi plot", command=stubPlot)
vizMenu.add_command(label="Heatmap", command=stubPlot)
vizMenu.add_command(label="Intersection matrix", command=stubPlot)
rootMenu.add_cascade(label="Visualizations",menu=vizMenu)


status = Label(root, bd=1, relief=SUNKEN, anchor=W)
status.config(text='Please select settings.')
status.pack(side=BOTTOM, fill=X)


root.mainloop()



def main():
    global dataDir
    global settingsFile
    parser = argparse.ArgumentParser()
    parser.add_argument('settings', default='', help='Path to settings XML file')
    args = parser.parse_args()
    
    if(args.settings):
        selectSettings(args.settings)
        openSettings()
        readData()
        calcStats()
        saveStats()

if __name__ == "__main__":
    main()
