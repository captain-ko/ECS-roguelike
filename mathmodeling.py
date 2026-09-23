import numpy as np
from typing import Type
width = 6
height = 6
parameters = ('s', 'i', 'r')
time = 30

a = 1
b = 1
c = 1
d = 1
e = 1


model = np.zeros((width, height, len(parameters)), dtype=float)

model[2,3,1] = .1


def run_model(model: np.array, time: int, a: float, b: float, c: float, d: float, e: float):

    for x, y, z in np.ndindex[model]:
        if z == [0]:
            model[x,y,z] = model[x,y,z] - (model[x,y,0]*(a*model[x,y,1]+b*model[x, y-1, 1]+c*model[x, y+1,1] + d*model[x-1, y, 1] + e*model[x+1,y,1]))
        if z == [1]:
            model[x,y,z] = (model[x,y,0]*(a*model[x,y,1]+b*model[x, y-1, 1]+c*model[x, y+1,1] + d*model[x-1, y, 1] + e*model[x+1,y,1]))

        if z == [2]:
            model[x,y,2] = model[x,y,2] + model[x,y,1]

    return model

print(run_model(model, 1, a, b, c, d, e))
