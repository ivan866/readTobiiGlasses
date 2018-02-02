import numpy as np


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


#TODO субтитры в виде облачков возле головы каждого испытуемого, а также анимированная лента жестов, P-S-R взятая из textgrid

gaze2=gaze[50000:50100]


vec=np.array(gaze[[    'Gaze 3D position left X',
                       'Gaze 3D position left Y',
                       'Gaze 3D position left Z',
                       'Gaze direction left X',
                       'Gaze direction left Y',
                       'Gaze direction left Z']])

X, Y, Z, U, V, W = zip(*vec)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.quiver(X, Y, Z, U, V, W)
# ax.set_xlim([0, 200])
# ax.set_ylim([200, 600])
# ax.set_zlim([300, 500])
plt.show()