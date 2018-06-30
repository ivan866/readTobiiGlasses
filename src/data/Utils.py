from datetime import datetime, date, time, timedelta

import pandas
from pandas import Series




def guessTimeFormat(val: object)-> str:
    """Helper method to determine the time strf string.
    
    :param val: Time string to try to parse.
    :return: Format string.
    """
    if type(val) is not str:
        val=str(val)

    formats = ['%H:%M:%S.%f', '%M:%S.%f', '%M:%S', '%S.%f', '%S']
    for fmt in formats:
        try:
            datetime.strptime(val, fmt)
        except ValueError:
            try:
                pandas.to_datetime(val, unit='s')
            except ValueError:
                continue
            break
        break
    #print('Time format of ' + val + ' string is guessed as ' + fmt + '.')
    return fmt


#FIXME valueerror if format =s.f and s>61
def parseTime(val: object=0) -> timedelta:
    """Helper method to convert time strings to datetime objects.

    Agnostic of time string format.

    :param val: Time string or float.
    :return: timedelta object.
    """
    val=str(val)
    fmt=guessTimeFormat(val)
    try:
        parsed=datetime.strptime(val, fmt)
    except ValueError:
        parsed=pandas.to_datetime(val, unit='s')
    return datetime.combine(date.min,parsed.time())-datetime.min


def parseTimeV(data:Series)->Series:
    """Vectorized version of parseTime method.

    :param data: pandas Series object.
    :return: Same object with values converted to timedelta.
    """
    if data.name=='Recording timestamp' or data.name=='Begin_Time' or data.name=='Begin Time - ss.msec':
        return pandas.to_timedelta(data.astype(float), unit='s')
    else:
        return pandas.to_datetime(data.astype(str), infer_datetime_format=True)-date.today()



# def formatTimedelta(delta:timedelta=timedelta(0))->str:
#     """Convert timedelta objects to str.
#
#     :param delta: timedelta object.
#     :return: str in M:S.f format
#     """
#     return (datetime.min+delta).strftime('%M:%S.%f')