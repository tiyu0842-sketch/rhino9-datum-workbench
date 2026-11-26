# -*- coding: utf-8 -*-
"""surfacefit_core 单元测试（纯 Python，不需要 Rhino）。"""

import os
import sys
import math
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import surfacefit_core as S


class TestVec(unittest.TestCase):
    def test_cross(self):
        self.assertEqual(S.cross((1, 0, 0), (0, 1, 0)), (0, 0, 1))

    def test_normalize_zero(self):
        self.assertEqual(S.normalize((0, 0, 0)), (0.0, 0.0, 0.0))


class TestFitPlane(unittest.TestCase):
    def test_flat_z(self):
        pts = [(x, y, 5.0) for x in range(-5, 6) for y in range(-5, 6)]
        p = S.fit_plane(pts)
        self.assertAlmostEqual(abs(p["normal"][2]), 1.0, places=4)
        self.assertAlmostEqual(p["origin"][2], 5.0, places=6)
        self.assertLess(p["rms"], 1e-9)

    def test_tilted_plane(self):
        # z = 0.5x + 0.2y + 3
        pts = [(x, y, 0.5 * x + 0.2 * y + 3.0)
               for x in range(-5, 6) for y in range(-5, 6)]
        p = S.fit_plane(pts)
        n = p["normal"]
        # 法向应与 (-0.5,-0.2,1) 平行
        expect = S.normalize((-0.5, -0.2, 1.0))
        cos = abs(S.dot(n, expect))
        self.assertGreater(cos, 0.9999)
        self.assertLess(p["rms"], 1e-9)

    def test_noisy_plane(self):
        # 加小噪声，RMS 应落在噪声量级
        pts = [(x, y, 3.0 + 0.01 * math.sin(x * 3 + y))
               for x in range(-5, 6) for y in range(-5, 6)]
        p = S.fit_plane(pts)
        self.assertLess(p["rms"], 0.02)
        self.assertGreater(p["rms"], 0.0)

    def test_too_few(self):
        self.assertIsNone(S.fit_plane([(0, 0, 0), (1, 1, 1)]))


class TestDeviation(unittest.TestCase):
    def test_stats(self):
        p = S.fit_plane([(x, y, 0) for x in range(-3, 4) for y in range(-3, 4)])
        pts = [(0, 0, 0.05), (1, 0, 0.2), (0, 1, 0.6)]
        s = S.deviation_stats(pts, p)
        self.assertAlmostEqual(s["max"], 0.6, places=6)
        self.assertAlmostEqual(s["within_0_1mm"], 1.0 / 3.0, places=6)


class TestCurvature(unittest.TestCase):
    def test_flat_grid(self):
        # 一个平坦的四边形网格（两个三角形）
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [[0, 1, 2], [0, 2, 3]]
        c0 = S.face_curvature(verts, faces, 0)
        c1 = S.face_curvature(verts, faces, 1)
        self.assertAlmostEqual(c0["normal"][2], 1.0, places=4)
        self.assertAlmostEqual(c1["normal"][2], 1.0, places=4)
        self.assertAlmostEqual(c0["gaussian"], 0.0, places=4)

    def test_filter(self):
        cs = [{"gaussian": 0.0}, {"gaussian": 0.5}, {"gaussian": 1.2}]
        self.assertEqual(S.filter_by_curvature(cs, k_max=0.6), [0, 1])
        self.assertEqual(S.filter_by_curvature(cs, k_min=0.6), [2])


class TestFacesToPoints(unittest.TestCase):
    def test_dedup(self):
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        faces = [[0, 1, 2], [0, 2, 3]]
        pts = S.faces_to_points(verts, faces, [0, 1])
        self.assertEqual(len(pts), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
