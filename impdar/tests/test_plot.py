#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 dlilien <dlilien@berens>
#
# Distributed under terms of the GNU GPL3.0 license.

"""
Test the machinery of plotting. We will not try the "show" lines.
"""
import sys
import os
import unittest
import numpy as np
from impdar.lib.RadarData import RadarData
from impdar.lib.Picks import Picks
from impdar.lib import plot
import matplotlib.pyplot as plt
if sys.version_info[0] >= 3:
    from unittest.mock import patch, MagicMock
else:
    from mock import patch, MagicMock

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class NoInitRadarData(RadarData):
    # This only exists so we can do tests on writing without reading

    def __init__(self):
        self.data = np.zeros((10, 20))
        # need to set this to avoid divide by zero later
        self.dt = 1
        self.dist = np.arange(20)
        self.lat = np.arange(20) * 2
        self.long = np.arange(20) * 3
        self.tnum = 20
        self.trace_num = np.arange(self.tnum) + 1.
        self.snum = 10
        self.travel_time = np.arange(10)


class DummyFig:
    # to mock saving
    def __init__(self):
        sfcalled = False

    def savefig(self, fn, dpi=None, ftype=None):
        sfcalled = True


def Any(cls):
    # to mock data argument in tests
    class Any(cls):
        def __init__(self):
            pass

        def __eq__(self, other):
            return True
    return Any()


class TestPlot(unittest.TestCase):
    
    @patch('impdar.lib.plot.plot_radargram', returns=[DummyFig(), None])
    def test_plotPLOTARGS(self, mock_plot_rad):
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')])
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='tnum', ydat='twtt', x_range=None)
        mock_plot_rad.reset_called()
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], xd=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='dist', ydat='twtt', x_range=None)
        mock_plot_rad.reset_called()
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], yd=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='tnum', ydat='depth', x_range=None)
        mock_plot_rad.reset_called()
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], xd=True, yd=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='dist', ydat='depth', x_range=None)
        mock_plot_rad.reset_called()

        # Check that we can save
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], xd=True, yd=True, s=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='dist', ydat='depth', x_range=None)
        mock_plot_rad.reset_called()

    @patch('impdar.lib.plot.plot_traces', returns=[DummyFig(), None])
    def test_plotPLOTTRACES(self, mock_plot_tr):
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], tr=0)
        mock_plot_tr.assert_called_with(Any(RadarData), 0, ydat='twtt')

    @patch('impdar.lib.plot.plot_power', returns=[DummyFig(), None])
    def test_plotPLOTPOWER(self, mock_plot_power):
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], power=0)
        mock_plot_power.assert_called_with(Any(RadarData), 0)

    @patch('impdar.lib.plot.plot_radargram', returns=[DummyFig(), None])
    def test_plotLOADGSSI(self, mock_plot_rad):
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'test_gssi.DZT')], gssi=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='tnum', ydat='twtt', x_range=None)

    @patch('impdar.lib.plot.plot_radargram', returns=[DummyFig(), None])
    def test_plotLOADPE(self, mock_plot_rad):
        plot.plot([os.path.join(THIS_DIR, 'input_data', 'test_pe.DT1')], pe=True)
        mock_plot_rad.assert_called_with(Any(RadarData), xdat='tnum', ydat='twtt', x_range=None)

    def test_plotBADINPUT(self):
        with self.assertRaises(ValueError):
            plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], gssi=True, pe=True)
        with self.assertRaises(ValueError):
            plot.plot([os.path.join(THIS_DIR, 'input_data', 'small_data.mat')], tr=0, power=1)


class TestPlotTraces(unittest.TestCase):
    
    def test_plot_traces(self):
        # Only checking that these do not throw errors
        dat = NoInitRadarData()
        fig, ax = plot.plot_traces(dat, 0)
        fig, ax = plot.plot_traces(dat, [1, 1])
        fig, ax = plot.plot_traces(dat, [1, 18])
        with self.assertRaises(ValueError):
            fig, ax = plot.plot_traces(dat, np.arange(10))
        with self.assertRaises(IndexError):
            fig, ax = plot.plot_traces(dat, 999)

        # no nmo
        fig, ax = plot.plot_traces(dat, 0, ydat='depth')

        # with nmo
        dat.nmo_depth = np.arange(10)
        fig, ax = plot.plot_traces(dat, 0, ydat='depth')
        with self.assertRaises(ValueError):
            fig, ax = plot.plot_traces(dat, 0, ydat='dum')

        # Make sure we handle axes rescaling ok
        dat.data[:, 0] = 10
        dat.data[:, 1] = -10
        fig, ax = plot.plot_traces(dat, (0, 2))


class TestPlotPower(unittest.TestCase):
    
    def test_plot_power(self):
        # Only checking that these do not throw errors
        dat = NoInitRadarData()
        with self.assertRaises(TypeError):
            fig, ax = plot.plot_power(dat, [12, 14])
        with self.assertRaises(ValueError):
            fig, ax = plot.plot_power(dat, 0)

        dat.picks = Picks(dat)
        dat.picks.add_pick(10)
        dat.picks.power[:] = 10
        # works with constant power
        fig, ax = plot.plot_power(dat, 10)

        with self.assertRaises(ValueError):
            fig, ax = plot.plot_power(dat, 0)
            
        # gets ok lims with variable power?
        dat.picks.power[:, 0] = 1
        fig, ax = plot.plot_power(dat, 10)


class TestPlotRadargram(unittest.TestCase):
    
    def test_plot_radargram_figaxin(self):
        # Only checking that these do not throw errors
        dat = NoInitRadarData()
        fig, ax = plot.plot_radargram(dat)

        fig, ax = plt.subplots()
        fig, ax = plot.plot_radargram(dat, fig=fig, ax=ax)
        fig, ax = plt.subplots()
        fig, ax = plot.plot_radargram(dat, fig=fig)


if __name__ == '__main__':
    unittest.main()