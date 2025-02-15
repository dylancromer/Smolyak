"""
This file contains the interpolation routines for the grids that are
built using the grid.py file in the smolyak package...  Write more doc
soon.
"""

from __future__ import division
import numpy as np
import numpy.linalg as la
from .grid import build_B

__all__ = ['find_theta', 'SmolyakInterp']


def find_theta(smolyak_grid, f_on_grid):
    """
    Given a SmolyakGrid object and the value of the function on the
    points of the grid, this function will return the coefficients theta
    """
    return la.solve(smolyak_grid.B_U, la.solve(smolyak_grid.B_L, f_on_grid))


class SmolyakInterp(object):
    """
    This class is going to take several inputs.  It will need a
    SmolyakGrid object to be passed in and the values of the function
    evaluated at the grid points
    """
    def __init__(self, smolyak_grid, f_on_grid):
        self.smolyak_grid = smolyak_grid
        self.f_on_grid = f_on_grid
        self.theta = find_theta(smolyak_grid, self.f_on_grid)

    def update_theta(self, f_on_grid):
        self.f_on_grid = f_on_grid
        self.theta = find_theta(self.smolyak_grid, self.f_on_grid)

    def interpolate(self, pts, interp=True, deriv=False, deriv_th=False, deriv_X=False):
        """
        Basic Lagrange interpolation, with optional first derivatives
        (gradient)

        Parameters
        ----------
        pts : array (float, ndim=2)
            A 2d array of points on which to evaluate the function. Each
            row is assumed to be a new d-dimensional point. Therefore, pts
            must have the same number of columns as ``si.smolyak_gridrid.d``

        interp : bool, optional(default=false)
            Whether or not to compute the actual interpolation values at pts

        deriv : bool, optional(default=false)
            Whether or not to compute the gradient of the function at each
            of the points. This will have the same dimensions as pts, where
            each column represents the partial derivative with respect to
            a new dimension.

        deriv_th : bool, optional(default=false)
            Whether or not to compute the ???? derivative with respect to the
            Smolyak polynomial coefficients (maybe?)

        deriv_X : bool, optional(default=false)
            Whether or not to compute the ???? derivative with respect to grid
            points


        Returns
        -------
        rets : list (array(float))
            A list of arrays containing the objects asked for. There are 4
            possible objects that can be computed in this function. They will,
            if they are called for, always be in the following order:

            1. Interpolation values at pts
            2. Gradient at pts
            3. ???? at pts
            4. ???? at pts

            If the user only asks for one of these objects, it is returned
            directly as an array and not in a list.


        Notes
        -----
        This is a stripped down port of ``dolo.SmolyakBasic.interpolate``

        TODO: There may be a better way to do this

        TODO: finish the docstring for the 2nd and 3rd type of derivatives

        """
        dim = pts.shape[1]
        smolyak_grid = self.smolyak_grid

        theta = self.theta
        transformed_points = smolyak_grid.dom2cube(pts)  # Move points to correct domain

        rets = []

        if deriv:
            new_B, der_B = build_B(dim, smolyak_grid.mu, transformed_points, smolyak_grid.pinds, True)
            vals = new_B.dot(theta)
            d_vals = np.tensordot(theta, der_B, (0, 0)).T

            if interp:
                rets.append(vals)

            radii = 2/(smolyak_grid.ub - smolyak_grid.lb)
            rets.append(d_vals*radii[None, :])

        ### this is all that is interesting for maszcal
        elif not deriv and interp:  # No derivs in build_B. Just do vals
            new_B = build_B(dim, smolyak_grid.mu, transformed_points, smolyak_grid.pinds)
            vals = new_B.dot(theta)
            rets.append(vals)
        ###

        if deriv_th:  # The derivative wrt the coeffs is just new_B
            if not interp and not deriv:  # we  haven't found this  yet
                new_B = build_B(dim, smolyak_grid.mu, transformed_points, smolyak_grid.pinds)
            rets.append(new_B)

        if deriv_X:
            if not interp and not deriv and not deriv_th:
                new_B = build_B(dim, smolyak_grid.mu, transformed_points, smolyak_grid.pinds)
            d_X = la.solve(smolyak_grid.B_L.T, la.solve(smolyak_grid.B_U.T, new_B.T)).T
            rets.append(d_X)

        if len(rets) == 1:
            rets = rets[0]

        return rets
