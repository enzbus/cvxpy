"""
Copyright 2013 Steven Diamond

This file is part of CVXPY.

CVXPY is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CVXPY is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CVXPY.  If not, see <http://www.gnu.org/licenses/>.
"""

from cvxpy.atoms.atom import Atom
import cvxpy.interface as intf
import cvxpy.lin_ops.lin_utils as lu
import numpy as np
import scipy.sparse as sp


class sum_largest(Atom):
    """Sum of the largest k values in the matrix X.
    """

    def __init__(self, x, k):
        self.k = k
        super(sum_largest, self).__init__(x)

    def validate_arguments(self):
        """Verify that k is a positive integer.
        """
        if int(self.k) != self.k or self.k <= 0:
            raise ValueError("Second argument must be a positive integer.")

    @Atom.numpy_numeric
    def numeric(self, values):
        """Returns the sum of the k largest entries of the matrix.
        """
        value = values[0].flatten()
        indices = np.argsort(-value)[:int(self.k)]
        return value[indices].sum()

    def _grad(self, values):
        """Gives the (sub/super)gradient of the atom w.r.t. each argument.

        Matrix expressions are vectorized, so the gradient is a matrix.

        Args:
            values: A list of numeric values for the arguments.

        Returns:
            A list of SciPy CSC sparse matrices or None.
        """
        # Grad: 1 for each of k largest indices.
        value = intf.from_2D_to_1D(values[0].flatten().T)
        indices = np.argsort(-value)[:int(self.k)]
        D = np.zeros((self.args[0].shape[0]*self.args[0].shape[1], 1))
        D[indices] = 1
        return [sp.csc_matrix(D)]

    def shape_from_args(self):
        """Returns the (row, col) shape of the expression.
        """
        return tuple()

    def sign_from_args(self):
        """Returns sign (is positive, is negative) of the expression.
        """
        # Same as argument.
        return (self.args[0].is_nonneg(), self.args[0].is_nonpos())

    def is_atom_convex(self):
        """Is the atom convex?
        """
        return True

    def is_atom_concave(self):
        """Is the atom concave?
        """
        return False

    def is_incr(self, idx):
        """Is the composition non-decreasing in argument idx?
        """
        return True

    def is_decr(self, idx):
        """Is the composition non-increasing in argument idx?
        """
        return False

    def get_data(self):
        """Returns the parameter k.
        """
        return [self.k]

    @staticmethod
    def graph_implementation(arg_objs, shape, data=None):
        """Reduces the atom to an affine expression and list of constraints.

        Parameters
        ----------
        arg_objs : list
            LinExpr for each argument.
        shape : tuple
            The shape of the resulting expression.
        data :
            Additional data required by the atom.

        Returns
        -------
        tuple
            (LinOp for objective, list of constraints)
        """
        # min sum(t) + kq
        # s.t. x <= t + q
        #      0 <= t
        x = arg_objs[0]
        k = lu.create_const(data[0], (1, 1))
        q = lu.create_var((1, 1))
        t = lu.create_var(x.shape)
        sum_t = lu.sum(t)
        obj = lu.sum_expr([sum_t, lu.mul_expr(k, q, (1, 1))])
        prom_q = lu.promote(q, x.shape)
        constr = [lu.create_leq(x, lu.sum_expr([t, prom_q])),
                  lu.create_geq(t)]
        return (obj, constr)