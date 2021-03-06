#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 dlilien <dlilien90@gmail.com>
#
# Distributed under terms of the GNU GPL-3.0 license.

"""
Test the machinery of process. This is broken up to match where it would likely fail; tests process wrappers of various methods are with the tests of those methods
"""
import os
import unittest
import numpy as np
from impdar.lib.NoInitRadarData import NoInitRadarData
from impdar.lib import process

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestConcat(unittest.TestCase):

    def test_concat(self):
        dats = process.concat([NoInitRadarData(), NoInitRadarData()])
        self.assertTrue(dats[0].data.shape == (2, 4))

        with self.assertRaises(ValueError):
            d2 = NoInitRadarData()
            d2.snum = 3
            dats = process.concat([NoInitRadarData(), d2])

        with self.assertRaises(ValueError):
            d2 = NoInitRadarData()
            d2.travel_time = np.array((2, 3))
            dats = process.concat([NoInitRadarData(), d2])


class TestProcess_and_exit(unittest.TestCase):

    def test_process_and_exitLOADMAT(self):
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')])

    def test_process_and_exitCAT(self):
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], cat=True)

    def test_process_and_exitPROCESS(self):
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], rev=True)

    def test_process_and_exitOUTNAMING(self):
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'data_raw.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], cat=True)
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'data_cat.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], cat=True)
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_cat.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), os.path.join(THIS_DIR, 'input_data', 'data_raw.mat')], rev=True)
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_proc.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'test_gssi.DZT')], filetype='gssi', rev=True)
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'input_data', 'test_gssi_proc.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'small_data.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], cat=True, o=os.path.join(THIS_DIR, 'small_data_cat.mat'))
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'small_data_cat.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'data_raw.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], cat=True, o=os.path.join(THIS_DIR, 'data_cat.mat'))
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'data_cat.mat')))
        process.process_and_exit([os.path.join(THIS_DIR, 'input_data', 'data_raw.mat'), os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], rev=True, o=THIS_DIR)
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'data_proc.mat')))
        self.assertTrue(os.path.exists(os.path.join(THIS_DIR, 'small_data_proc.mat')))

    def tearDown(self):
        if os.path.exists(os.path.join(THIS_DIR, 'small_data_cat.mat')):
            os.remove(os.path.join(THIS_DIR, 'small_data_cat.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_cat.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'small_data_cat.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'small_data_proc.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'small_data_proc.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'small_data_proc.mat')):
            os.remove(os.path.join(THIS_DIR, 'small_data_proc.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'data_proc.mat')):
            os.remove(os.path.join(THIS_DIR, 'data_proc.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'data_proc.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'data_proc.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'data_cat.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'data_cat.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'data_cat.mat')):
            os.remove(os.path.join(THIS_DIR, 'data_cat.mat'))
        if os.path.exists(os.path.join(THIS_DIR, 'input_data', 'test_gssi_proc.mat')):
            os.remove(os.path.join(THIS_DIR, 'input_data', 'test_gssi_proc.mat'))


if __name__ == '__main__':
    unittest.main()
