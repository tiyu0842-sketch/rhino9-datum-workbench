# -*- coding: utf-8 -*-
"""双筛链测试：法向(NFF)+曲率(m2s)→拟合→偏差。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import chain_core as C


def box_mesh(w=10.0, d=8.0, h=6.0):
    """6 面盒子，面序：底(-Z)/顶(+Z)/前(-Y)/右(+X)/后(+Y)/左(-X)。"""
    verts = [(0, 0, 0), (w, 0, 0), (w, d, 0), (0, d, 0),
             (0, 0, h), (w, 0, h), (w, d, h), (0, d, h)]
    faces = [[0, 3, 2, 1],   # -Z
             [4, 5, 6, 7],   # +Z
             [0, 1, 5, 4],   # -Y
             [1, 2, 6, 5],   # +X
             [2, 3, 7, 6],   # +Y
             [3, 0, 4, 7]]   # -X
    return verts, faces


class TestChain(unittest.TestCase):
    def setUp(self):
        self.verts, self.faces = box_mesh()

    def test_top_plane(self):
        # 选朝上(+Z)且平的：应只拿到顶面(面1)，拟合 z=6
        r = C.run_chain(self.verts, self.faces, direction=(0, 0, 1),
                        angle_deg=30, k_max=1.0, rms_tolerance=0.5,
                        verbose=False)
        self.assertIn(1, r["normal_kept"])
        self.assertIn(1, r["curvature_kept"])
        self.assertEqual(r["candidates"], [1])
        self.assertTrue(r["accepted"], r["reason"])
        self.assertAlmostEqual(r["plane"]["origin"][2], 6.0, places=4)
        self.assertAlmostEqual(abs(r["plane"]["normal"][2]), 1.0, places=3)

    def test_include_opposite(self):
        # 双向模式：顶面+底面都命中，但因为两层面间距 6mm，RMS 会超大→不合格
        r = C.run_chain(self.verts, self.faces, direction=(0, 0, 1),
                        angle_deg=30, include_opposite=True, k_max=1.0,
                        rms_tolerance=0.5, verbose=False)
        self.assertIn(0, r["normal_kept"])
        self.assertIn(1, r["normal_kept"])
        self.assertEqual(set(r["candidates"]), {0, 1})
        self.assertFalse(r["accepted"])  # 两面拟合出的平面RMS=3mm

    def test_vertical_faces(self):
        # 选朝前(-Y)：面2，拟合 y=0
        r = C.run_chain(self.verts, self.faces, direction=(0, -1, 0),
                        angle_deg=30, k_max=1.0, rms_tolerance=0.5,
                        verbose=False)
        self.assertEqual(r["candidates"], [2])
        self.assertTrue(r["accepted"])
        self.assertAlmostEqual(abs(r["plane"]["origin"][1]), 0.0, places=4)

    def test_strict_angle_no_hit(self):
        r = C.run_chain(self.verts, self.faces, direction=(0, 0, 1),
                        angle_deg=5, min_angle_deg=10, k_max=1.0,
                        verbose=False)
        self.assertFalse(r["accepted"])
        self.assertIn("法向筛", r["reason"])

    def test_summary(self):
        r = C.run_chain(self.verts, self.faces, k_max=1.0, verbose=False)
        s = C.summarize(r)
        self.assertTrue(s.startswith("未通过") or s.startswith("通过"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
