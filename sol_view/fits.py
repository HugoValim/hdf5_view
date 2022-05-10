from lmfit.models import GaussianModel, LinearModel
import numpy as np


def fitGauss(xarray, yarray):
    """
    This function mix a Linear Model with a Gaussian Model (LMFit).
    See also: `Lmfit Documentation <http://cars9.uchicago.edu/software/python/lmfit/>`_
    Parameters
    ----------
    xarray : array
        X data
    yarray : array
        Y data
    Returns
    -------
    peak value: `float`
    peak position: `float`
    min value: `float`
    min position: `float`
    fwhm: `float`
    fwhm positon: `float`
    center of mass: `float`
    fit_Y: `array`
    fit_result: `ModelFit`
    """
    y = yarray
    x = xarray
    gaussMod = GaussianModel()
    linMod = LinearModel()
    pars = linMod.make_params(intercept=y.min(), slope=0)
    pars += linMod.guess(y, x=x)
    pars += gaussMod.guess(y, x=x)
    mod = gaussMod + linMod
    fwhm = 0
    fwhm_position = 0
    try:
        result = mod.fit(y, pars, x=x)
        fwhm = result.values["fwhm"]
        fwhm_position = result.values["center"]
    except ValueError:
        result = None
    peak_position = xarray[np.argmax(y)]
    peak = np.max(y)
    minv_position = x[np.argmin(y)]
    minv = np.min(y)
    COM = (np.multiply(x, y).sum()) / y.sum()
    return (peak, peak_position, minv, minv_position, fwhm, fwhm_position, COM, result)
