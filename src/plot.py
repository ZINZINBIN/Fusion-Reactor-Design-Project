import numpy as np
import matplotlib.pyplot as plt
from src.device import Tokamak
from scipy.interpolate import RectBivariateSpline, interp2d
from matplotlib import colors, cm
from matplotlib.pyplot import Axes
from matplotlib.gridspec import GridSpec
from typing import Dict, Union

# KSTAR configuration
KSTAR_PF_coils = {
    "P1L":[0.57, -0.25],
    "P1U":[0.57, 0.25],
    "P2L":[0.57, -0.7],
    "P2U":[0.57, 0.7],
    "P3L":[0.57, -1.00],
    "P3U":[0.57, 1.00],
    "P4L":[0.57, -1.26],
    "P4U":[0.57, 1.26],
    "P5L":[1.09, -2.30],
    "P5U":[1.09, 2.30],
    "P6L":[3.09, -1.92],
    "P6U":[3.09, 1.92],
    "P7L":[3.73, -0.98],
    "P7U":[3.73, 0.98],
}

KSTAR_limiter_shape = np.array([
    [ 1.265,  1.085],
    [ 1.608,  1.429],
    [ 1.683,  1.431],
    [ 1.631,  1.326],
    [ 1.578,  1.32 ],
    [ 1.593,  1.153],
    [ 1.626,  1.09 ],
    [ 2.006,  0.773],
    [ 2.233,  0.444],
    [ 2.235,  0.369],
    [ 2.263,  0.31 ],
    [ 2.298,  0.189],
    [ 2.316,  0.062],
    [ 2.316, -0.062],
    [ 2.298, -0.189],
    [ 2.263, -0.31 ],
    [ 2.235, -0.369],
    [ 2.233, -0.444],
    [ 2.006, -0.773],
    [ 1.626, -1.09 ],
    [ 1.593, -1.153],
    [ 1.578, -1.32 ],
    [ 1.631, -1.326],
    [ 1.683, -1.431],
    [ 1.608, -1.429],
    [ 1.265, -1.085],
    [ 1.265,  1.085]
])

# draw limiter
def draw_limiter(ax:Axes, limiter_shape:np.array):
    ax.plot(limiter_shape[:,0], limiter_shape[:,1], 'black')
    ax.set_xlabel('R[m]')
    ax.set_ylabel('Z[m]')
    return ax