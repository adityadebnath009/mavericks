import numpy as np
from scipy.interpolate import griddata

# Dummy data
points = np.array([[10, 70], [10, 71], [11, 70], [11, 71]])
values = np.array([50, 60, 70, 80])

grid_x, grid_y = np.mgrid[10:11:0.25, 70:71:0.25]
grid_z0 = griddata(points, values, (grid_x, grid_y), method='linear')

print(grid_z0)
