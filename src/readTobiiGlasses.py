##указать путь к файлам с экспортированными данными
workPath='G:/text/org/ИЯ РАН/exportData'
participantIds=['Project1 Data Export_02']

workDirs=workPath
gazedataFiles=[workDirs+'/'+participantId+'.tsv' for participantId in participantIds]

cameraWidthPx=1920
cameraHeightPx=1080


##считываем данные
with open(gazedataFiles[0],encoding='UTF-16') as gazedataFile:
    gazedataFile.readline()
    data=gazedataFile.readline()
print(data)
