#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 dlilien <dlilien90@gmail.com>
#
# Distributed under terms of the GNU GPL-3.0 license.

"""
Test the basics of RadarData
"""
import os
import unittest
import numpy as np
from impdar.lib.RadarData import RadarData
from impdar.lib import process

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestRadarDataLoading(unittest.TestCase):

    def test_ReadSucceeds(self):
        data = RadarData(os.path.join(THIS_DIR, 'input_data', 'small_data.mat'))
        self.assertEqual(data.data.shape, (20, 40))

    def tearDown(self):
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'test_out.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'test_out.mat'))


class TestRadarDataMethods(unittest.TestCase):

    def setUp(self):
        self.data = RadarData(os.path.join(THIS_DIR, 'input_data', 'small_data.mat'))
        self.data.x_coord = np.arange(40)
        self.data.travel_time = np.arange(0, 0.2, 0.01)
        self.data.dt = 1.0e-8
        self.data.trig = 0.

    def test_Reverse(self):
        data_unrev = self.data.data.copy()
        self.data.reverse()
        self.assertTrue(np.allclose(self.data.data, np.fliplr(data_unrev)))
        self.assertTrue(np.allclose(self.data.x_coord, np.arange(39, -1, -1)))
        self.data.reverse()
        self.assertTrue(np.allclose(self.data.data, data_unrev))
        self.assertTrue(np.allclose(self.data.x_coord, np.arange(40)))

    def test_process_Reverse(self):
        data_unrev = self.data.data.copy()
        process.process([self.data], rev=True)
        self.assertTrue(np.allclose(self.data.data, np.fliplr(data_unrev)))
        self.assertTrue(np.allclose(self.data.x_coord, np.arange(39, -1, -1)))
        process.process([self.data], rev=True)
        self.assertTrue(np.allclose(self.data.data, data_unrev))
        self.assertTrue(np.allclose(self.data.x_coord, np.arange(40)))

    def test_CropTWTT(self):
        self.data.crop(0.165, 'bottom', dimension='twtt')
        self.assertTrue(self.data.data.shape == (17, 40))
        self.data.crop(0.055, 'top', dimension='twtt')
        self.assertTrue(self.data.data.shape == (11, 40))

        # do not fail on bad flags
        self.data.flags.crop = False
        self.data.crop(0.055, 'top', dimension='twtt')
        self.assertTrue(self.data.flags.crop.shape == (3,))
        self.assertTrue(self.data.flags.crop[0])

    def test_CropErrors(self):
        with self.assertRaises(ValueError):
            self.data.crop(0.165, 'bottom', dimension='dummy')
        with self.assertRaises(ValueError):
            self.data.crop(0.165, 'dummy', dimension='twtt')

    def test_CropSNUM(self):
        self.data.crop(17, 'bottom', dimension='snum')
        self.assertTrue(self.data.data.shape == (17, 40))
        self.data.crop(6, 'top', dimension='snum')
        self.assertTrue(self.data.data.shape == (11, 40))

    def test_CropTrigInt(self):
        self.data.trig = 2
        with self.assertRaises(ValueError):
            self.data.crop(17, 'bottom', dimension='pretrig')
        self.data.crop(6, 'top', dimension='pretrig')
        self.assertTrue(self.data.data.shape == (18, 40))

    def test_CropTrigMat(self):
        self.data.trig = np.ones((40,), dtype=int)
        self.data.trig[20:] = 2
        self.data.crop(6, 'top', dimension='pretrig')
        self.assertTrue(self.data.data.shape == (19, 40))

    def test_CropDepthOnTheFly(self):
        self.data.crop(0.165, 'bottom', dimension='depth', uice=2.0e6)
        self.assertTrue(self.data.data.shape == (17, 40))
        self.data.crop(0.055, 'top', dimension='depth', uice=2.0e6)
        self.assertTrue(self.data.data.shape == (11, 40))

    def test_CropDepthWithNMO(self):
        self.data.nmo(0., uice=2.0e6, uair=2.0e6)
        self.data.crop(0.165, 'bottom', dimension='depth')
        self.assertTrue(self.data.data.shape == (17, 40))
        self.data.crop(0.055, 'top', dimension='depth')
        self.assertTrue(self.data.data.shape == (11, 40))

    def test_process_Crop(self):
        with self.assertRaises(TypeError):
            process.process([self.data], crop=True)
        with self.assertRaises(ValueError):
            process.process([self.data], crop=(1.0, 'top', 'dum'))
        with self.assertRaises(ValueError):
            process.process([self.data], crop=(1.0, 'bot', 'snum'))
        with self.assertRaises(ValueError):
            process.process([self.data], crop=('ugachacka', 'top', 'snum'))
        process.process([self.data], crop=(17, 'bottom', 'snum'))
        self.assertTrue(self.data.data.shape == (17, 40))
        process.process([self.data], crop=(6, 'top', 'snum'))
        self.assertTrue(self.data.data.shape == (11, 40))

    def test_agc(self):
        self.data.agc()
        self.assertTrue(self.data.flags.agc)

    def test_rangegain(self):
        self.data.rangegain(1.0)
        self.assertTrue(self.data.flags.rgain)
        self.data.flags.rgain = False

        self.data.trig = np.zeros((self.data.tnum, ))
        self.data.rangegain(1.0)
        self.assertTrue(self.data.flags.rgain)

    def test_NMO_noexcpetion(self):
        # If velocity is 2
        self.data.nmo(0., uice=2.0, uair=2.0)
        self.assertTrue(np.allclose(self.data.travel_time * 1.0e-6, self.data.nmo_depth))
        # shouldn't care about uair if offset=0
        self.data.nmo(0., uice=2.0, uair=200.0)
        self.assertTrue(np.allclose(self.data.travel_time * 1.0e-6, self.data.nmo_depth))

        self.data.flags.nmo = False
        self.data.nmo(0., uice=2.0, uair=200.0)
        self.assertEqual(self.data.flags.nmo.shape, (2,))
        self.assertTrue(self.data.flags.nmo[0])

    def test_process_NMO(self):
        # If velocity is 2
        process.process([self.data], nmo=(0., 2.0, 2.0))
        self.assertTrue(np.allclose(self.data.travel_time * 1.0e-6, self.data.nmo_depth))
        # shouldn't care about uair if offset=0
        process.process([self.data], nmo=(0., 2.0, 200.0))
        self.assertTrue(np.allclose(self.data.travel_time * 1.0e-6, self.data.nmo_depth))

        # Just make sure we can use one arg
        process.process([self.data], nmo=0.)

    def test_restack_odd(self):
        self.data.restack(5)
        self.assertTrue(self.data.data.shape == (20, 8))

    def test_restack_even(self):
        self.data.restack(4)
        self.assertTrue(self.data.data.shape == (20, 8))

    def test_process_restack(self):
        process.process([self.data], restack=3)
        self.assertTrue(self.data.data.shape == (20, 13))
        process.process([self.data], restack=[3])
        self.assertTrue(self.data.data.shape == (20, 4))

    def test_elev_correct(self):
        self.data.elev = np.arange(self.data.data.shape[1]) * 0.002
        with self.assertRaises(ValueError):
            self.data.elev_correct()
        self.data.nmo(0, 2.0e6)
        self.data.elev_correct(v_avg=2.0e6)
        self.assertTrue(self.data.data.shape == (27, 40))

    def test_constant_space(self):
        distlims = (self.data.dist[0], self.data.dist[-1])
        space = 100.
        self.data.constant_space(space)
        self.assertTrue(self.data.data.shape == (20, np.ceil((distlims[-1] - distlims[0]) * 1000. / space)))
        self.assertTrue(self.data.x_coord.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))
        self.assertTrue(self.data.y_coord.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))
        self.assertTrue(self.data.lat.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))
        self.assertTrue(self.data.long.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))
        self.assertTrue(self.data.elev.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))
        self.assertTrue(self.data.decday.shape == (np.ceil((distlims[-1] - distlims[0]) * 1000. / space), ))

        # do not fail because flags structure is weird from matlab
        space = 100.
        self.data.flags.interp = False
        self.data.constant_space(space)
        self.assertTrue(self.data.flags.interp.shape == (2,))
        self.assertTrue(self.data.flags.interp[0])
        self.assertEqual(self.data.flags.interp[1], space)

    def tearDown(self):
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'test_out.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'test_out.mat'))


if __name__ == '__main__':
    unittest.main()
