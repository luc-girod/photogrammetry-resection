# Author:  Jeffrey T. Walton, Paul Smith's College, New York
#
#   Single-photo resection - calculates the camera orientation and location
#       given camera calibration parameters, control point photo and world
#        coordinates and initial guesses for camera exterior orientation.
#
#   based on MATLAB code from:
#   Introduction to Modern Photogrammetry by Mikhail, Bethel, McGlone
#   John Wiley & Sons, Inc. 2001

import sys
import numpy as np
from scipy.optimize import minimize


def collinearity_eqn_residual(iop,eop,x,y,X,Y,Z):
    """
    Usage:
        collinearity_eqn_residual(iop,eop,x,y,X,Y,Z)

    Inputs:
        iop = dict of interior orientation parameters: x0, y0, f
        eop = dict of exterior orientation parameters: omega, phi, kappa, XL, YL, ZL
        x = array of x photo coordinates of control points
        y = array of y photo coordinates of control points
        X = array of X world coordinates of control points
        Y = array of Y world coordinates of control points
        Z = array of Z world coordinates of control points

    Returns:
        residuals in x and y collinearity equations for a single point as a tuple
    """
    from math import sin, cos
    x0 = iop['x0']
    y0 = iop['y0']
    focallength = iop['f']

    om = eop['omega']
    ph = eop['phi']
    kp = eop['kappa']

    XL = eop['XL']
    YL = eop['YL']
    ZL = eop['ZL']

    Mom = np.matrix([[1, 0, 0], [0, cos(om), sin(om)], [0, -sin(om), cos(om)]])
    Mph = np.matrix([[cos(ph), 0, -sin(ph)], [0, 1, 0], [sin(ph), 0, cos(ph)]])
    Mkp = np.matrix([[cos(kp), sin(kp), 0], [-sin(kp), cos(kp), 0], [0, 0, 1]])

    M = Mkp * Mph * Mom

    uvw = M * np.matrix([[X-XL], [Y-YL], [Z-ZL]])

    resx = x - x0 + focallength * uvw[0,0] / uvw[2,0]
    resy = y - y0 + focallength * uvw[1,0] / uvw[2,0]

    return resx, resy


class CollinearityData:
    """
    class to store data for the collinearity equations
    """
    def __init__(self, camera_file, point_file):
        """
        initilizes data for collinearity equations

        reads camera parameters from camera_file
        reads control point data from point_file
        """

        f = open(camera_file,'r')
        dat = np.loadtxt(f,float)
        f.close

        self.eop = {}

        # data from lines 1-3 of the camera_file
        self.eop['omega'] = dat[0]
        self.eop['phi'] = dat[1]
        self.eop['kappa'] = dat[2]

        # data from lines 4-6 of the camera_file
        self.eop['XL'] = dat[3]
        self.eop['YL'] = dat[4]
        self.eop['ZL'] = dat[5]

        self.iop = {}

        # data from lines 7-9 of the camera_file
        self.iop['x0'] = dat[6]
        self.iop['y0'] = dat[7]
        self.iop['f'] = dat[8]

        self.label = []
        x = []
        y = []
        X = []
        Y = []
        Z = []

        f = open(point_file,'r')
        for line in f:
            l = line.split()
            # each line has 6 values: label, x, y, X, Y, Z (whitespace delimited)
            self.label.append(l[0])
            x.append(float(l[1]))
            y.append(float(l[2]))
            X.append(float(l[3]))
            Y.append(float(l[4]))
            Z.append(float(l[5]))
        f.close

        self.x = np.array(x)
        self.y = np.array(y)
        self.X = np.array(X)
        self.Y = np.array(Y)
        self.Z = np.array(Z)



def coll_func(indep_vars):
    """
    collinearity function calculates a sum of the squared residuals of the
        collinearity equations for all of the control points
    This function is passed to scipy.optimize.minimize()

    Inputs:
        indep_vars (passed) are the exterior orientation parameters of the camera
        data (global) camera interior calibration data, photo points, control points

    Returns:
        sum of squared residuals of collinearity eqns
    """
    global data
    iop = data.iop
    #eop = data.eop
    label = data.label
    x = data.x
    y = data.y
    X = data.X
    Y = data.Y
    Z = data.Z

    eop = {}
    eop['omega'] = indep_vars[0]
    eop['phi'] = indep_vars[1]
    eop['kappa'] = indep_vars[2]
    eop['XL'] = indep_vars[3]
    eop['YL'] = indep_vars[4]
    eop['ZL'] = indep_vars[5]

    i = 0
    F = 0.0
    for l in label:

        F1, F2 = collinearity_eqn_residual(iop,eop,x[i],y[i],X[i],Y[i],Z[i])
        F += F1**2 + F2**2
        i += 1

    return F


if len(sys.argv) > 1:
    camera_file = sys.argv[1]
else:
    #camera_file = 'E://WebcamFinse//Cucza//CamCucza.inp'
    camera_file = 'E://WebcamFinse//CamFinseInit.inp'
if len(sys.argv) > 2:
    point_file = sys.argv[2]
else:
    #point_file = 'E://WebcamFinse//Cucza//GCPs_Centered.inp'
    point_file = 'E://WebcamFinse//GCPs_WebcamFinse_Centered.inp'
data = CollinearityData(camera_file, point_file)

x0 = np.zeros(6)
# initilaize guesses for eop as read from file
eop = data.eop
x0[0] = eop['omega']
x0[1] = eop['phi']
x0[2] = eop['kappa']
x0[3] = eop['XL']
x0[4] = eop['YL']
x0[5] = eop['ZL']

eps = np.array([4.8e-06, 4.8e-06, 4.8e-06, 1.0e-01, 1.0e-01, 1.0e-01]) # numerical differentiation step size
res = minimize(coll_func, x0, jac=False, method='BFGS', options={'eps': eps, 'disp': True})
#res = minimize(coll_func, x0, options={'disp': True})

#print res.x
print('Solution:')
print('omega, ', res.x[0])
print('phi, ', res.x[1])
print('kappa, ', res.x[2])
print('XL, ', res.x[3])
print('YL, ', res.x[4])
print('ZL, ', res.x[5])
