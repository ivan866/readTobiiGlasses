# Read Tobii Glasses

В программе использован модуль pandas. Если вы работаете под Windows, рекомендуется установить дистрибутив Anaconda Python 3 (<http://continuum.io/downloads>).


## Данные

Данные айтрекинга необходимо экспортировать через Tobii ProLab в формат tsv. При экспорте нужно отметить галочки для Gaze point, Gaze direction, Pupil diameter, фиксаций, гироскопа и акселерометра. Рекомендуется убрать галочки для Project name, Participant name, Export date, Recording duration, Fixation filter name, etc.

Аннотации из ELAN необходимо экспортировать в формат txt (File>Export as>Tab-delimeted Text). Обязательно при экспорте отметить галочки Separate column for each tier, Include time column for Begin time, Duration; Include time format ss.msec. ВАЖНО: обязательно снять галочку Repeat values of annotations spanning other annotations.

Аннотации глаз типа ocul можно оставить в формате Excel.

Из столбцов времени считываются абсолютные значения, как привязанные к общему нулю для всех каналов для данного участника. При этом столбец с временной меткой не обязательно должен начинаться с 0:00.000, но это значение должно иметь привязку к общему нулю.


## Описание файла settings.xml

Данный файл содержит список всех файлов с данными, которые требуется подвергнуть анализу, а также временные границы этапов эксперимента. Рекомендуется скопировать данный файл в папку с данными, после чего внести в него изменения в соответствии с пакетом данных.

Поле zeroTime указывается для тех файлов, временная метка в которых начинается не с момента первого этапа, т.е. тех, которые еще не обрезаны. Обычно в пакете данных перед началом анализа уже произведена обрезка, поэтому данное поле нужно только в файлах типа ey и gaze (данные с айтрекера). Если несколько файлов имеют одинаковые временные поправки, укажите zeroTime только для одного файла. Остальным назначьте в качестве значения zeroTime ссылку на тип файла, содержащего такую же дельту.

Порядок полей interval играет роль при подсчете их временных границ. Длительности этапов складываются, начиная с первого, позволяя вычислить момент начала и конца каждого этапа, и при этом файл не содержит избыточных данных и потенциальных ошибок из-за двусмысленности полей.

Все временные параметры рекомендуется указывать в формате 0:00.000

Если требуется исключить какой-то файл из анализа, просто удалите всю строку <file>.