import numpy as np

# Create a limit based on volume over the last x days at x percentile
def volume_limit(volume, percentile, days):
    return np.percentile(volume[-days:], percentile)
