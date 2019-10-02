import numpy as np
import pandas as pd
import laspy


def bin_points(points, d):
    """ Subsets points to resolution of d intervals """
    return np.floor(points/d)*d


def create_profile(x, bins=None):
    """ Create a profile for a set of points. Requires there to be a Zbin

    """
    counts, bin_edges = np.histogram(x, bins=bins)
    return np.mean(counts)


# Load the file
filename = 'uhnb3mes_rotate_scale.las'
working_dir = '/Users/kellycaylor/Documents/dev/sfm/'

las_file = laspy.file.File(working_dir + filename)


XYZ = pd.DataFrame({
        'X': las_file.X,
        'Y': las_file.Y,
        'Z': las_file.Z
        })

XYZ.X = XYZ.X/100
XYZ.Y = XYZ.Y/100
XYZ.Z = XYZ.Z/100


#  Here is where we "make" subplots

dxy = 5.  # 2 meter bins in X and Y directions
dz = 0.5  # 0.5 meter bins in vertical.

XYZ['Xbin'] = bin_points(XYZ.X, dxy)
XYZ['Ybin'] = bin_points(XYZ.Y, dxy)
XYZ['Zbin'] = bin_points(XYZ.Z, dz)

# Groupby is the magic.
max_height = XYZ.groupby(['Xbin', 'Ybin'])['Z'].max()
n_points = XYZ.groupby(['Xbin', 'Ybin'])['Z'].count()


groups = XYZ.groupby(['Xbin', 'Ybin'])['Z', 'Zbin']

# Make profiles for each subplot
z_bins = np.arange(0, np.ceil(np.max(XYZ.Z)), dz) + dz
profiles = XYZ.groupby(['Xbin', 'Ybin'])['Z'].pipe(create_profile, bins=z_bins)

