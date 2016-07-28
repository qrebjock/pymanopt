import unittest

import numpy as np
import numpy.linalg as la
import numpy.testing as np_testing

from pymanopt.manifolds import FixedRankEmbedded


class TestFixedRankEmbeddedManifold(unittest.TestCase):
    def setUp(self):
        self.m = m = 10
        self.n = n = 5
        self.k = k = 3
        self.man = FixedRankEmbedded(m, n, k)

    def test_dim(self):
        assert self.man.dim == (self.m + self.n - self.k) * self.k

    def test_typicaldist(self):
        assert self.man.dim == self.man.typicaldist

    def test_dist(self):
        e = self.man
        a = e.rand()
        x = e.randvec(a)
        y = e.randvec(a)
        with self.assertRaises(NotImplementedError):
            e.dist(x, y)

    def test_inner(self):
        e = self.man
        x = e.rand()
        a = e.randvec(x)
        b = e.randvec(x)
        A = x[0].dot(a[1].dot(x[2].T)) + a[0].dot(x[2].T) + x[0].dot(a[2].T)
        B = x[0].dot(b[1].dot(x[2].T)) + b[0].dot(x[2].T) + x[0].dot(b[2].T)
        trueinner = np.sum(A*B)
        np_testing.assert_almost_equal(trueinner, e.inner(x, a, b))

    def test_proj_range(self):
        m = self.man
        x = m.rand()
        v = np.random.randn(self.m, self.n)

        g = m.proj(x, v)
        # Check that g is a true tangent vector
        np_testing.assert_allclose(np.dot(g[0].T, x[0]),
                                   np.zeros((self.k, self.k)),
                                   atol=1e-6)
        np_testing.assert_allclose(np.dot(g[2].T, x[2]),
                                   np.zeros((self.k, self.k)),
                                   atol=1e-6)

    def test_proj(self):
        # Verify that proj gives the closest point within the tangent space
        # by displacing the result slightly and checking that this increases
        # the distance.
        m = self.man
        x = self.man.rand()
        v = np.random.randn(self.m, self.n)

        g = m.proj(x, v)
        # Displace g a little
        g_disp = g + 0.01 * m.randvec(x)

        # Return to the ambient representation
        g = m.tangent2ambient(x, g)
        g_disp = m.tangent2ambient(x, g_disp)
        g = g[0].dot(g[1]).dot(g[2].T)
        g_disp = g_disp[0].dot(g_disp[1]).dot(g_disp[2].T)

        assert np.linalg.norm(g - v) < np.linalg.norm(g_disp - v)

    def test_proj_tangents(self):
        # Verify that proj leaves tangent vectors unchanged
        e = self.man
        x = e.rand()
        u = e.randvec(x)
        A = e.proj(x, e.tangent2ambient(x, u))
        B = u
        # diff = [A[k]-B[k] for k in xrange(len(A))]
        np_testing.assert_allclose(A[0], B[0])
        np_testing.assert_allclose(A[1], B[1])
        np_testing.assert_allclose(A[2], B[2])

    def test_norm(self):
        e = self.man
        x = e.rand()
        u = e.randvec(x)
        np_testing.assert_almost_equal(np.sqrt(e.inner(x, u, u)), e.norm(x, u))

    def test_rand(self):
        e = self.man
        x = e.rand()
        y = e.rand()
        assert np.shape(x[0]) == (self.m, self.k)
        assert np.shape(x[1]) == (self.k, self.k)
        assert np.shape(x[2]) == (self.n, self.k)
        np_testing.assert_allclose(x[0].T.dot(x[0]), np.eye(self.k), atol=1e-6)
        np_testing.assert_allclose(x[2].T.dot(x[2]), np.eye(self.k), atol=1e-6)
        np_testing.assert_allclose(np.diag(np.diag(x[1])), x[1])
        for k in range(len(x)):
            assert la.norm(x[k] - y[k]) > 1e-6

    def test_transp(self):
        s = self.man
        x = s.rand()
        y = s.rand()
        u = s.randvec(x)
        A = s.transp(x, y, u)
        B = s.proj(y, s.tangent2ambient(x, u))
        diff = [A[k]-B[k] for k in range(len(A))]
        np_testing.assert_almost_equal(s.norm(y, diff), 0)

    def test_apply_ambient(self):
        m = self.man
        z = np.random.randn(self.m, self.n)

        # Set u, s, v so that z = u.dot(s).dot(v.T)
        u, s, v = np.linalg.svd(z, full_matrices=False)
        s = np.diag(s)
        v = v.T

        w = np.random.randn(self.n, self.n)

        np_testing.assert_allclose(z.dot(w), m._apply_ambient(z, w))
        np_testing.assert_allclose(z.dot(w), m._apply_ambient((u, s, v), w))

    def test_apply_ambient_transpose(self):
        m = self.man
        z = np.random.randn(self.n, self.m)

        # Set u, s, v so that z = u.dot(s).dot(v.T)
        u, s, v = np.linalg.svd(z, full_matrices=False)
        s = np.diag(s)
        v = v.T

        w = np.random.randn(self.n, self.n)

        np_testing.assert_allclose(z.T.dot(w),
                                   m._apply_ambient_transpose(z, w))
        np_testing.assert_allclose(z.T.dot(w),
                                   m._apply_ambient_transpose((u, s, v), w))

    def test_tangent2ambient(self):
        m = self.man
        x = m.rand()
        z = m.randvec(x)

        z_ambient = (x[0].dot(z[1]).dot(x[2].T) + z[0].dot(x[2].T) +
                     x[0].dot(z[2].T))

        u, s, v = m.tangent2ambient(x, z)

        np_testing.assert_allclose(z_ambient, u.dot(s).dot(v.T))

    def test_ehess2rhess(self):
        m = self.man
        x = m.rand()
        h = m.randvec(x)
        egrad, ehess = np.random.randn(2, self.m, self.n)

        up, M, vp = m.proj(x, ehess)

        T = egrad.dot(h[2]).dot(np.linalg.inv(x[1]))
        up += T - x[0].dot(x[0].T.dot(T))
        T = egrad.T.dot(h[0]).dot(np.linalg.inv(x[1]))
        vp += T - x[2].dot(x[2].T.dot(T))

        rhess = m.ehess2rhess(x, egrad, ehess, h)

        np_testing.assert_allclose(up, rhess[0])
        np_testing.assert_allclose(M, rhess[1])
        np_testing.assert_allclose(vp, rhess[2])

    def test_retr(self):
        # Test that the result is on the manifold and that for small
        # tangent vectors it has little effect.
        x = self.man.rand()
        u = self.man.randvec(x)

        y = self.man.retr(x, u)

        np_testing.assert_allclose(y[0].T.dot(y[0]), np.eye(self.k), atol=1e-6)
        np_testing.assert_allclose(y[2].T.dot(y[2]), np.eye(self.k), atol=1e-6)
        np_testing.assert_allclose(np.diag(np.diag(y[1])), y[1])

        u = u * 1e-6
        y = self.man.retr(x, u)
        y = y[0].dot(y[1]).dot(y[2].T)

        u = self.man.tangent2ambient(x, u)
        u = u[0].dot(u[1]).dot(u[2].T)
        x = x[0].dot(x[1]).dot(x[2].T)

        np_testing.assert_allclose(y, x + u, atol=1e-5)

    def test_egrad2rgrad(self):
        # Verify that egrad2rgrad and proj are equivalent.
        e = self.man
        x = e.rand()
        u, s, v = np.linalg.svd(np.random.randn(self.m, self.n),
                                full_matrices=False)
        s = np.diag(s)
        v = v.T
        u = (u, s, v)

        np_testing.assert_allclose(e.egrad2rgrad(x, u)[0], e.proj(x, u)[0])
        np_testing.assert_allclose(e.egrad2rgrad(x, u)[1], e.proj(x, u)[1])
        np_testing.assert_allclose(e.egrad2rgrad(x, u)[2], e.proj(x, u)[2])

    def test_randvec(self):
        e = self.man
        x = e.rand()
        u = e.randvec(x)

        # Check that u is a tangent vector
        assert np.shape(u[0]) == (self.m, self.k)
        assert np.shape(u[1]) == (self.k, self.k)
        assert np.shape(u[2]) == (self.n, self.k)
        np_testing.assert_allclose(np.dot(u[0].T, x[0]),
                                   np.zeros((self.k, self.k)),
                                   atol=1e-6)
        np_testing.assert_allclose(np.dot(u[2].T, x[2]),
                                   np.zeros((self.k, self.k)),
                                   atol=1e-6)

        v = e.randvec(x)

        np_testing.assert_almost_equal(e.norm(x, u), 1)
        assert e.norm(x, u - v) > 1e-6
