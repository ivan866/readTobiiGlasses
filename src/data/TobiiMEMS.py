import numpy as np
import pandas as pd
from pandas import DataFrame

from skinematics.imus import IMU_Base



class TobiiMEMS(IMU_Base):

    """Reads in gyroscope and accelerometer data from Tobii Glasses 2. Retrieves 3D position analytically."""


    # FIXME this method should parse file, not dataframe
    def get_data(self, data:DataFrame, rate:int=100)->None:
        """Parses gyroscope data. Sets inner class data fields.

        :param data: gyro data from DataReader
        :param rate: overall frequency after interpolation or filling
        :return:
        """

        # interpolate with a given rate
        # dur=data.iloc[-1,0]-data.iloc[0,0]
        # dt = 1 / np.float(rate)
        # t_lin = np.arange(0, dur, dt)
        #
        #
        # data_interp = pd.DataFrame()
        # for ii in range(1,7):
        #     # FIXME column name hard-coded
        #     data_interp[data.keys()[ii]] = np.interp(t_lin * 1000, data['Recording timestamp'], data.ix[:, ii])
        # data_interp['time'] = t_lin
        #
        # # Set the conversion factors by hand, and apply them
        # # TODO откуда эти коэффициенты, проверить
        # conversions = {}
        # conversions['acc'] = 0.061 / 1000
        # conversions['gyr'] = 4.375 / 1000 * np.pi / 180
        #
        # data_interp.iloc[:, 1:4] *= conversions['acc']
        # data_interp.iloc[:, 4:7] *= conversions['gyr']
        #
        #
        #
        # returnValues = [rate]
        #
        # # Extract the columns that you want, by name
        # paramList = ['acc', 'gyr']
        # for param in paramList:
        #     Expression = param + '*'
        #     returnValues.append(data_interp.filter(regex=Expression).values)
        #
        # self._set_info(*returnValues)

        pass



    # def _set_data(self, data):
    #     """С версии v.0.6.8 данный метод переопределять не нужно.
    #
    #     :param data:
    #     :return:
    #     """
    #     self.rate = data['rate']
    #     self.acc = data['acc']
    #     self.omega = data['omega']
    #     self.source = None
    #     self._set_info(self.rate,self.acc,self.omega,None)
