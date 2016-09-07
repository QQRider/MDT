import itertools
import numpy as np
from matplotlib.gridspec import GridSpec

from mdt.visualization.dict_conversion import SimpleClassConversion, IntConversion

__author__ = 'Robbert Harms'
__date__ = "2016-09-02"
__maintainer__ = "Robbert Harms"
__email__ = "robbert.harms@maastrichtuniversity.nl"


class GridLayout(object):

    def __init__(self):
        super(GridLayout, self).__init__()
        self._spacings = dict(left=0.06, right=0.90, top=0.97, bottom=0.04, wspace=0.5)

    @classmethod
    def get_conversion_info(cls):
        return SimpleClassConversion(cls, cls._get_attribute_conversions())

    @classmethod
    def _get_attribute_conversions(cls):
        return {}

    def get_gridspec(self, figure, nmr_plots):
        """Get the grid layout specifier for the given figure using the given number of plots.

        Args:
            figure (Figure): the figure to add the axis to
            nmr_plots (int): the total number of plots

        Returns:
            GridLayoutSpecifier: the specifier we can ask new subplot axis from
        """

    def __eq__(self, other):
        if not isinstance(other, GridLayout):
            return NotImplemented
        return isinstance(other, type(self))

    def __ne__(self, other):
        return not self.__eq__(other)


class GridLayoutSpecifier(object):

    def __init__(self, gridspec, figure, positions=None):
        """Create a grid layout specifier using the given gridspec and the given figure.

        Args:
            gridspec (GridSpec): the gridspec to use
            figure (Figure): the figure to generate subplots for
            positions (list): if given, a list with grid spec indices for every requested axis
        """
        self.gridspec = gridspec
        self.figure = figure
        self.positions = positions

    def get_axis(self, index):
        gridspec_ind = self.gridspec[index]
        if self.positions is not None:
            gridspec_ind = self.gridspec[self.positions[index]]
        return self.figure.add_subplot(gridspec_ind)


class AutoGridLayout(GridLayout):

    def get_gridspec(self, figure, nmr_plots):
        rows, cols = self._get_row_cols_square(nmr_plots)
        return GridLayoutSpecifier(GridSpec(rows, cols, **self._spacings), figure)

    def _get_row_cols_square(self, nmr_plots):
        defaults = ((1, 1), (1, 2), (1, 3), (2, 2), (2, 3), (2, 3), (2, 3))
        if nmr_plots < len(defaults):
            return defaults[nmr_plots - 1]
        else:
            cols = np.ceil(nmr_plots / 3.0)
            rows = np.ceil(float(nmr_plots) / cols)
            rows = int(rows)
            cols = int(cols)
        return rows, cols


class Rectangular(GridLayout):

    def __init__(self, rows=None, cols=None):
        super(Rectangular, self).__init__()
        self.rows = rows
        self.cols = cols

        if self.rows is not None:
            self.rows = int(self.rows)
            if self.rows < 1:
                raise ValueError('The number of rows ({}) can not be smaller than 1.'.format(self.rows))

        if self.cols is not None:
            self.cols = int(self.cols)
            if self.cols < 1:
                raise ValueError('The number of columns ({}) can not be smaller than 1.'.format(self.rows))

    @classmethod
    def _get_attribute_conversions(cls):
        return {'rows': IntConversion(),
                'cols': IntConversion()}

    def get_gridspec(self, figure, nmr_plots):
        rows = self.rows
        cols = self.cols

        if rows is None and cols is None:
            return AutoGridLayout().get_gridspec(figure, nmr_plots)

        if rows is None:
            rows = int(np.ceil(nmr_plots / cols))
        if cols is None:
            cols = int(np.ceil(nmr_plots / rows))

        if rows * cols < nmr_plots:
            cols = int(np.ceil(nmr_plots / rows))

        return GridLayoutSpecifier(GridSpec(rows, cols, **self._spacings), figure)

    def __eq__(self, other):
        if not isinstance(other, GridLayout):
            return NotImplemented
        return isinstance(other, type(self)) and other.rows == self.rows and other.cols == self.cols


class LowerTriangular(GridLayout):

    def __init__(self):
        super(LowerTriangular, self).__init__()

    def get_gridspec(self, figure, nmr_plots):
        size, positions = self._get_size_and_position(nmr_plots)
        return GridLayoutSpecifier(GridSpec(size, size, **self._spacings), figure, positions=positions)

    def _get_size_and_position(self, nmr_plots):
        size = self._get_lowest_triangle_length(nmr_plots)

        positions = []
        for x, y in itertools.product(range(size), range(size)):
            if x >= y:
                positions.append(x * size + y)

        return size, positions

    @staticmethod
    def _get_lowest_triangle_length(nmr_plots):
        for n in range(1, nmr_plots):
            if 0.5 * (n ** 2 + n) >= nmr_plots:
                return n
        return nmr_plots


class SingleColumn(GridLayout):

    def get_gridspec(self, figure, nmr_plots):
        return GridLayoutSpecifier(GridSpec(nmr_plots, 1, **self._spacings), figure)


class SingleRow(GridLayout):

    def get_gridspec(self, figure, nmr_plots):
        return GridLayoutSpecifier(GridSpec(1, nmr_plots, **self._spacings), figure)