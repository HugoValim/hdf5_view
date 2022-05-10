import numpy
from silx.gui.plot.actions import PlotAction


class Derivative(PlotAction):
    """QAction performing a Fourier transform on all curves when checked,
    and reverse transform when unchecked.

    :param plot: PlotWindow on which to operate
    :param parent: See documentation of :class:`QAction`
    """

    def __init__(self, plot, parent=None):
        PlotAction.__init__(
            self,
            plot,
            icon="shape-circle",
            text="Derivative",
            tooltip="Perform derivative on all curves",
            triggered=self.DerivativeAllCurves,
            checkable=True,
            parent=parent,
        )

    def DerivativeAllCurves(self, checked=False):
        """Get all curves from our PlotWindow, compute the amplitude spectrum
        using a Fast Fourier Transform, replace all curves with their
        amplitude spectra.

        When un-checking the button, do the reverse transform.

        :param checked: Boolean parameter signaling whether the action
            has been checked or unchecked.
        """
        allCurves = self.plot.getAllCurves()

        # self.plot.clearCurves()

        for curve in allCurves:
            x, y, legend, info = curve[0:4]
            # x = curve.getXData()
            # y = curve.getYData()
            # legend = curve.getLegend()
            # info = curve.getInfo()
            if info is None:
                info = {}

            if checked:
                dx = x[1] - x[0]
                dydx = numpy.gradient(y, dx)

                # plot the amplitude spectrum
                self.plot.addCurve(x, dydx, legend="Derivative of " + legend, info=info)

            else:
                if "Derivative" in legend:
                    self.plot.removeCurve(legend)

        self.plot.resetZoom()
