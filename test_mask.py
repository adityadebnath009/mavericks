from global_land_mask import globe
import numpy as np

# Mumbai (Land)
print("Mumbai is land:", globe.is_land(19.07, 72.87))
# Arabian Sea (Ocean)
print("Arabian Sea is land:", globe.is_land(18.0, 70.0))
