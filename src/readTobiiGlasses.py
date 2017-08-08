import os
import argparse
import datetime
import subprocess
#import re

from tkinter import *
from tkinter import filedialog

import xml.etree.ElementTree as ET

#import numpy
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

    #читаем данные об интервалах
    intervals = settings.findall("interval")
    if len(intervals)==0:
        status.config(text='No intervals specified. Assuming monolythic data.')
        root.update_idletasks()


    #основная структура данных
    data['availColumns']={}
    data['gaze']={}
    data['fixations']={}
    data['saccades']={}
    data['eyesNotFounds']={}
    data['unclassifieds']={}
    data['gyro']={}
    data['accel']={}
    data['voc'] = {}
    data['manu'] = {}
    data['ceph'] = {}
    data['ocul'] = {}

    settingsGaze=settings.findall("file[@type='gaze']")
    if len(settingsGaze):
        for file in settingsGaze:
            gazeFile=dataDir+'/'+file.get('path')
            status.config(text='Reading gaze data (file '+os.path.basename(gazeFile)+')...')
            root.update_idletasks()
            #узнаем какие столбцы присутствуют
            headers=pandas.read_table(gazeFile,nrows=1,encoding='UTF-16')
            availColumns=[i for i in list(headers.columns) if re.match('Recording timestamp|Gaze point|Gaze direction|Pupil diameter|Eye movement type|Gaze event duration|Fixation point|Gyro|Accelerometer',i)]
            data['availColumns'][file.get('id')]=availColumns
            gazeData=pandas.read_table(gazeFile,decimal=",",encoding='UTF-16',
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
            if 'Gyro X' and 'Gyro Y' and 'Gyro Z' in availColumns:
                gyro=gazeData[['Recording timestamp',
                               'Gyro X','Gyro Y','Gyro Z']]
                #убираем пустые строки, но без учета столбца времени
                gyro.dropna(subset=(['Gyro X','Gyro Y','Gyro Z']),how='all',inplace=True)
                data['gyro'][file.get('id')]=gyro

                #гироскоп в основных данных больше не нужен
                gazeData.drop(['Gyro X','Gyro Y','Gyro Z'],axis=1,inplace=True)

            if 'Accelerometer X' and 'Accelerometer Y' and 'Accelerometer Z' in availColumns:
                accel = gazeData[['Recording timestamp',
                                  'Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']]
                accel.dropna(subset=(['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z']), how='all', inplace=True)
                data['accel'][file.get('id')]=accel

                gazeData.drop(['Accelerometer X', 'Accelerometer Y', 'Accelerometer Z'], axis=1, inplace=True)

            # убираем пустые строки
            gazeData = gazeData[(gazeData['Gaze point X'].notnull()) & (gazeData['Gaze point Y'].notnull()) | \
                                (gazeData['Eye movement type'] == 'EyesNotFound')]


            if 'Eye movement type' in availColumns:
                #вырезаем строки с фиксациями
                fixations=gazeData.loc[gazeData['Eye movement type']=='Fixation'][['Recording timestamp',
                                                                                   'Gaze event duration','Eye movement type index',
                                                                                   'Fixation point X','Fixation point Y']]
                #удаляем одинаковые строки, но без учета первого столбца
                fixations.drop_duplicates(fixations.columns[range(1,fixations.shape[1])],inplace=True)
                timeReadable=pandas.to_datetime(fixations['Recording timestamp'],unit='s')
                fixations.insert(1,'Timecode',timeReadable.dt.strftime('%M:%S.%f'))
                data['fixations'][file.get('id')]=fixations


                #теперь саккады
                #при частоте 50 Гц координаты начала и конца саккад не достоверны
                # def calcSaccadeGazePoints(row):
                #     prevPosInd=numpy.where(gazeData['Recording timestamp']<row['Recording timestamp'])[0][-1]
                #     prevX=gazeData.iloc[prevPosInd]['Gaze point X']
                #     prevY=gazeData.iloc[prevPosInd]['Gaze point Y']
                #     row['Start gaze point X']=prevX
                #     row['Start gaze point Y']=prevY
                #
                #     nextPosInd=numpy.where(gazeData['Recording timestamp']>=((row['Recording timestamp']+row['Gaze event duration']).round(6)))[0][0]
                #     nextX=gazeData.iloc[nextPosInd]['Gaze point X']
                #     nextY=gazeData.iloc[nextPosInd]['Gaze point Y']
                #     row['End gaze point X']=nextX
                #     row['End gaze point Y']=nextY
                #
                #     return row

                saccades=gazeData.loc[gazeData['Eye movement type']=='Saccade'][['Recording timestamp',
                                                                                 'Gaze event duration','Eye movement type index']]
                saccades.drop_duplicates(saccades.columns[range(1,saccades.shape[1])],inplace=True)
                # status.config(text='Parsing saccades (file '+os.path.basename(gazeFile)+')...')
                # root.update_idletasks()
                # saccades=saccades.apply(calcSaccadeGazePoints,axis=1)
                # saccades=saccades[['Recording timestamp',
                #                    'Gaze event duration','Eye movement type index',
                #                    'Start gaze point X','Start gaze point Y',
                #                    'End gaze point X','End gaze point Y']]
                # timeReadable=pandas.to_datetime(saccades['Recording timestamp'],unit='s')
                # saccades.insert(1,'Timecode',timeReadable.dt.strftime('%M:%S.%f'))
                data['saccades'][file.get('id')]=saccades


                #участки потерянного контакта
                eyesNotFounds=gazeData.loc[gazeData['Eye movement type']=='EyesNotFound'][['Recording timestamp',
                                                                                           'Gaze event duration','Eye movement type index']]
                eyesNotFounds.drop_duplicates(eyesNotFounds.columns[range(1,eyesNotFounds.shape[1])],inplace=True)
                data['eyesNotFounds'][file.get('id')]=eyesNotFounds

                #неизвестные события
                unclassifieds=gazeData.loc[gazeData['Eye movement type']=='Unclassified'][['Recording timestamp',
                                                                                           'Gaze point X','Gaze point Y',
                                                                                           'Gaze event duration','Eye movement type index']]
                unclassifieds.drop_duplicates(unclassifieds.columns[range(1,unclassifieds.shape[1])],inplace=True)
                data['unclassifieds'][file.get('id')]=unclassifieds


                #события в основных данных больше не нужны
                gazeData.drop(['Eye movement type','Gaze event duration','Eye movement type index',
                               'Fixation point X','Fixation point Y'],
                                axis=1,inplace=True)


            data['gaze'][file.get('id')]=gazeData
    else:
        status.config(text='No gaze data specified in settings.')
        root.update_idletasks()



    # читаем аннотации manu
    settingsManu = settings.findall("file[@type='manu']")
    if len(settingsManu):
        status.config(text='Reading manu annotations...')
        root.update_idletasks()
        for file in settingsManu:
            manuFile = dataDir + '/' + file.get('path')
            status.config(text='Reading manu annotation (file ' + os.path.basename(manuFile) + ')...')
            root.update_idletasks()
            manuData = pandas.read_table(manuFile,skiprows=2)
            data['manu'][file.get('id')] = manuData
    else:
        status.config(text='No manu annotations specified in settings.')
        root.update_idletasks()



    #читаем аннотации ocul из excel
    settingsOcul=settings.findall("file[@type='ocul']")
    if len(settingsOcul):
        status.config(text='Reading ocul annotations...')
        root.update_idletasks()
        for file in settingsOcul:
            oculFile=dataDir+'/'+file.get('path')
            status.config(text='Reading ocul annotation (file '+os.path.basename(oculFile)+')...')
            root.update_idletasks()
            oculData=pandas.read_excel(oculFile,header=None,
                                       names=('Timecode',
                                              'Gaze event duration',
                                              'Id','Tier'),
                                       parse_cols='B:E')
            data['ocul'][file.get('id')]=oculData
    else:
        status.config(text='No ocul annotations specified in settings.')
        root.update_idletasks()

        
    status.config(text='All valuable data read successfully.')





def validateData():
    pass



def checkSettings():
    if settings:
        return True
    else:
        status.config(text='Read settings and data first.')
        return False
def checkData():
    if data:
        return True
    else:
        status.config(text='Read data first.')
        return False

#сохраняем фиксации и саккады в файл
def exportFixations(format):
    if checkSettings() and checkData():
        written = False
        for file in settings.findall("file[@type='gaze']"):
            if 'Eye movement type' in data['availColumns'][file.get('id')]:
                written=True
                fixFile=os.path.splitext(file.get('path'))[0]+'_Fixations.'+format
                sacFile=os.path.splitext(file.get('path'))[0]+'_Saccades.'+format
                if format=='csv':
                    data['fixations'][file.get('id')].to_csv(dataDir+'/'+fixFile,sep='\t',index=False)
                    data['saccades'][file.get('id')].to_csv(dataDir+'/'+sacFile,sep='\t',index=False)
                elif format=='xls':
                    data['fixations'][file.get('id')].to_excel(dataDir+'/'+fixFile,index=False)
                    data['saccades'][file.get('id')].to_excel(dataDir+'/'+sacFile,index=False)
        if written:
            status.config(text='Fixations and saccades saved to files. Note that data before zeroTime is still present in exported data.')
        else:
            status.config(text='There is no data to write.')
    
def exportGyro():
    if checkSettings() and checkData():
        written = 0
        for file in settings.findall("file[@type='gaze']"):
            if 'Gyro X' in data['availColumns'][file.get('id')] and 'Gyro Y' in data['availColumns'][file.get('id')] and 'Gyro Z' in data['availColumns'][file.get('id')]:
                written=written+1
                gyroFile=os.path.splitext(file.get('path'))[0]+'_Gyro.csv'
                status.config(text='Writing gyro data (file '+os.path.basename(gyroFile)+')...')
                root.update_idletasks()
                data['gyro'][file.get('id')].to_csv(dataDir+'/'+gyroFile,sep='\t',index=False)
            if 'Accelerometer X' in data['availColumns'][file.get('id')] and 'Accelerometer Y' in data['availColumns'][file.get('id')] and 'Accelerometer Z' in data['availColumns'][file.get('id')]:
                written=written+10
                accelFile=os.path.splitext(file.get('path'))[0]+'_Accelerometer.csv'
                status.config(text='Writing accelerometer data (file ' + os.path.basename(accelFile) + ')...')
                root.update_idletasks()
                data['accel'][file.get('id')].to_csv(dataDir+'/'+accelFile,sep='\t',index=False)
        if written==1:
            status.config(text='Available gyroscope data saved to files. Note that data before zeroTime is still present in exported data.')
        elif written==10:
            status.config(text='Available accelerometer data saved to files. Note that data before zeroTime is still present in exported data.')
        elif written==11:
            status.config(text='Both available gyroscope and accelerometer data saved to files. Note that data before zeroTime is still present in exported data.')
        else:
            status.config(text='There is no sensor data to write.')




#stats
def descriptiveStats():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    dateTag = ET.Element('date')
    dateTag.text = now
    settings.append(dateTag)

    saveDir = dataDir + '/stats_' + now
    os.mkdir(saveDir)

    for channel in data['ocul']:
        for interval in settings.findall("interval"):
            dataChannel=data['ocul'][channel]
            dataChannel['Timecode']<datetime.datetime.strptime(interval.get('duration'),'%M:%S.%f').time()


    settingsTree.write(saveDir + '/' + os.path.basename(settingsFile))
    status.config(text='Statistics report saved. Settings included for reproducibility.')



# report=Text(root)
# report.insert('0.0','test')
# report.config(state=DISABLED)
# report.pack(side=LEFT,anchor=NW)
# status.config(text='Select all, then Ctrl+C to copy. Or Statistics>Save report.')



def saveStats():
    pass





#viz
videoEyWidthPx=1920
videoEyHeightPx=1080
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
exportMenu = Menu(dataMenu,tearoff=0)
exportMenu.add_command(label="Fixation lines to CSV", command=lambda: exportFixations('csv'))
exportMenu.add_command(label="Fixation lines to Excel", command=lambda: exportFixations('xls'))
exportMenu.add_command(label="Gyroscope data", command=exportGyro)
dataMenu.add_cascade(label="Export",menu=exportMenu)
dataMenu.add_command(label="Validation", command=validateData)
rootMenu.add_cascade(label="Data",menu=dataMenu)

statsMenu = Menu(rootMenu,tearoff=0)
statsMenu.add_command(label="Descriptive", command=descriptiveStats)
#экспортируем и сразу открываем
#statsMenu.add_command(label="Save report to Excel", command=saveStats)
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
    
    if args.settings:
        selectSettings(args.settings)
        openSettings()
        readData()
        calcStats()
        saveStats()

if __name__ == "__main__":
    main()
