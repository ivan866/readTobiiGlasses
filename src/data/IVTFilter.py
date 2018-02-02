import numpy as np

import pandas as pd
from pandas import DataFrame


from eyestudio.Engine.Filter import Filter



class IVTFilter(Filter):

    """Receives angular velocity on input and outputs intervals above threshold."""


    def __init__(self):
        super().__init__()

        self.state = None
        self.last_state = None

        print('I-VT filter started.')


    #def parameters(self):
    #    return [
    #        Parameter(name='threshold', caption='Threshold [deg/s]', vartype=float, default=77.0),
    #        Parameter(name='dur_threshold', caption='Min dur [ms]', vartype=float, default=100.0),
    #    ]


    def printParams(self)->str:
        """Returns a str describing the parameters set.

        :return: all parameters for this filter.
        """
        res=[]
        for k,v in self.params.items():
            res.append('{0}: {1}'.format(k,v))

        return '; '.join(res)


    def reset(self,len:int)->None:
        """Clears result.

        :param len: data length
        :return: None
        """
        self.result=[float('nan') for i in range(len)]




    def process(self, data:DataFrame, setFixation=None)->None:
        """Main filtering routine.

        :param data: timestamp (s), angular velocity (deg/s) component
        :param setFixation: result appending handler
        :return: None
        """
        self.reset(data.shape[0])

        thresh = self.getParameter('min_velocity')
        minTime = self.getParameter('min_static')

        if setFixation is None:
            setFixation=self.setFixation

        fixationStart = 0
        ordinal=0
        for index in range(data.shape[0]):
            time= data.iloc[index, 0]
            theta=abs(data.iloc[index, 1])


            if theta < thresh:
                self.state = Filter.FIXATION

                if self.last_state != self.state:
                    ordinal=ordinal+1
                    fixationStart = index
            else:
                if self.last_state == Filter.FIXATION:
                    # Check if it's long enough
                    dur = time - data.iloc[fixationStart, 0]
                    if dur < minTime:
                        ordinal = ordinal - 1
                        # Make all into saccades again
                        for i in range(fixationStart, index):
                            setFixation(time, i, self.SACCADE, theta, ordinal)

                self.state = Filter.SACCADE

            self.last_state = self.state
            setFixation(time, index, self.state, theta, ordinal)



    def setFixation(self,time:float,index:int,state:int,theta:float,ordinal:int)->None:
        """Result handler that appends found intervals.

        :param self:
        :param time: timestamp (s)
        :param index: row index
        :param state: oculomotor event code from eyestudio.Engine.Filter
        :param theta: data point actual value
        :param ordinal: state order number
        :return: None
        """
        self.result[index]=(time,state,theta,ordinal)



    #----
    def getResultFiltered(self,state:str=''):
        '''Groups result by State and Ordinal, yielding starting and ending time of motions.

        :param state: which state to return
        :return: DataFrame with start/end timestamps for each ordinal or None
        '''
        result=DataFrame(self.result,columns=['Timestamp','State','Value','Ordinal'])
        grouped=result.groupby(by=['State','Ordinal'],sort=True)
        aggregated=grouped['Timestamp'].agg(['count','min','max'])
        aggregated2=grouped['Value'].agg(['mean'])
        concatenated=pd.concat((aggregated, aggregated2), axis=1)
        #motion offsets
        data=result['Value']
        level=self.getParameter('noise_level')
        tmin=[]
        tmax=[]
        if len(concatenated.index.levels[0])>1:
            for index,row in concatenated.loc[1].iterrows():
                sindex=result[result['Timestamp']==row['min']].index[0]
                eindex=result[result['Timestamp']==row['max']].index[0]
                traversed=self.traverseOffsets(data=data,sindex=sindex,eindex=eindex,thres=level)
                tmin.append(result.iloc[traversed[0]]['Timestamp'])
                tmax.append(result.iloc[traversed[1]]['Timestamp'])
            #расширяем границы
            concatenated.loc[1]['min']=tmin
            concatenated.loc[1]['max']=tmax
        #filtering
        concatenated=self.filterValues(concatenated)
        if state=='stills':
            return concatenated.loc[0]
        elif state=='motions':
            if len(concatenated.index.levels[0]) > 1:
                return concatenated.loc[1]
            else:
                return pd.DataFrame()
        elif state=='':
            return concatenated
        else:
            raise ValueError('state specified wrong.')


    def traverseOffsets(self,data,sindex:int,eindex:int,thres:float)->tuple:
        """Runs step by step through data in given direction and finds nearest threshold value.

        :param data:
        :param sindex: start index
        :param eindex: end index
        :param thres: value to search for
        :return: found indices
        """
        myRange = data[:sindex]
        myRange=myRange[myRange<=thres]
        if len(myRange):
            svalue=myRange.index[-1]
        else:
            svalue=data.index[0]

        myRange = data[eindex:]
        myRange=myRange[myRange<=thres]
        if len(myRange):
            evalue=myRange.index[0]
        else:
            evalue=data.index[-1]

        return (svalue,evalue)


    #удаляем слишком короткие движения
    def filterValues(self,values:DataFrame)->DataFrame:
        """Filter out results based on condition.

        :param values: data to filter
        :return: filtered data
        """
        dur=[]
        minMotion=self.getParameter('min_motion')
        values.apply(lambda x: dur.append(x['max'] - x['min']), axis=1)
        values['dur']=dur
        res=values[values['dur']>=minMotion]
        return res
