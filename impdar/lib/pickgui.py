#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 David Lilien <dlilien90@gmail.com>
#
# Distributed under terms of the GNU GPL3.0 license.

from .ui import RawPickGUI
from . import plot, RadarData, picklib
import numpy as np
import os.path
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.figure import Figure
import sys
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5, QtGui
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
else:
    from matplotlib.backends.backend_qt4agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
    from PyQt4.QtWidgets import QFileDialog, QMessageBox


def pick(radardata, guard_save=True, xd=False, yd=False):
    if xd:
        x = 'dist'
    else:
        x = 'tracenum'
    if yd:
        y = 'depth'
    else:
        y = 'twtt'

    if not hasattr(radardata, 'picks') or radardata.picks is None:
        radardata.picks = RadarData.Picks(radardata)

    app = QtWidgets.QApplication(sys.argv)
    ip = InteractivePicker(radardata, xdat=x, ydat=y)
    ip.show()
    sys.exit(app.exec_())


class InteractivePicker(QtWidgets.QMainWindow, RawPickGUI.Ui_MainWindow):

    def __init__(self, dat, xdat='tracenum', ydat='twtt', x_range=(0, -1), guard_save=False):
        # Next line is required for Qt, then give us the layout
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # Connect the menu to actions
        self.actionSave_pick.triggered.connect(self._save_as)
        self.actionSave_as.triggered.connect(self._save_as)
        self.actionClose.triggered.connect(self.close)

        # Connect controls on the left
        self.ColorSelector.currentTextChanged.connect(self._color_select)

        # Easy access to normal mpl figure and axes
        self.ax = self.FigCanvasWidget.canvas.ax
        self.fig = self.FigCanvasWidget.canvas.fig
        plt.ion()

        # Two constants to keep track of how to prompt for saves
        self.fn = None
        self._saved = True

        # Set defaults
        self.bwb = 'bwb'
        self.freq = 4
        self.pick_mode = 'select'

        # line is the matplotlib object of the current pick
        self.cline = []
        self.tline = []
        self.bline = []

        # pick_pts contains our picked points, which will differ from what we want to save in the file. Need to have one per line.
        self.pick_pts = []
        self.dat = dat
        self.current_layer = 0
        self.current_pick = None

        if self.dat.picks is not None and self.dat.picks.samp1 is not None:
            self.pick_pts = [p[~np.isnan(p)].tolist() for p in self.dat.picks.samp1]

        try:
            if xdat not in ['tracenum', 'dist']:
                raise ValueError('x axis choices are tracenum or dist')
            if ydat not in ['twtt', 'depth']:
                raise ValueError('y axis choices are twtt or depth')

            if x_range is None:
                x_range = (0, -1)
            if x_range[-1] == -1:
                x_range = (x_range[0], self.dat.tnum)

            self.lims = np.percentile(dat.data[:, x_range[0]:x_range[-1]], (10, 90))
            self.clims = [self.lims[0] * 2 if self.lims[0] < 0 else self.lims[0] / 2, self.lims[1] * 2]
            self.minSpinner.setValue(self.lims[0])
            self.maxSpinner.setValue(self.lims[1])
            self.FrequencySpin.setValue(self.dat.picks.pickparams.freq)

            if hasattr(dat.flags, 'elev') and dat.flags.elev:
                yd = dat.elevation
                self.ax.set_ylabel('Elevation (m)')
            else:
                self.ax.invert_yaxis()
                if ydat == 'twtt':
                    self.yd = dat.travel_time
                    self.ax.set_ylabel('Two way travel time (usec)')
                elif ydat == 'depth':
                    if dat.nmo_depth is not None:
                        self.yd = dat.nmo_depth
                    else:
                        self.yd = dat.travel_time / 2.0 * 1.69e8 * 1.0e-6
                    self.ax.set_ylabel('Depth (m)')

            if xdat == 'tracenum':
                self.xd = np.arange(int(self.dat.tnum))[x_range[0]:x_range[-1]]
                self.ax.set_xlabel('Trace number')
            elif xdat == 'dist':
                self.xd = self.dat.dist[x_range[0]:x_range[-1]]
                self.ax.set_xlabel('Distance (km)')

            self.im = self.ax.imshow(dat.data[:, x_range[0]:x_range[-1]], cmap=plt.cm.gray_r, vmin=self.lims[0], vmax=self.lims[1], extent=[np.min(self.xd), np.max(self.xd), np.max(self.yd), np.min(self.yd)], aspect='auto')
            if self.dat.picks.samp1 is not None:
                self.cline = []
                self.bline = []
                self.tline = []
                for i in range(self.dat.picks.samp1.shape[0] - 1):
                    self.cline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp2[i, :])], self.yd[self.dat.picks.samp2[i, :][~np.isnan(self.dat.picks.samp1[i, :])].astype(int)], color='b', picker=5)[0])
                    self.tline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp1[i, :])], self.yd[self.dat.picks.samp1[i, :][~np.isnan(self.dat.picks.samp2[i, :])].astype(int)], color='y')[0])
                    self.bline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp3[i, :])], self.yd[self.dat.picks.samp3[i, :][~np.isnan(self.dat.picks.samp3[i, :])].astype(int)], color='y')[0])
                self.cline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp2[-1, :])], self.yd[self.dat.picks.samp2[-1, :][~np.isnan(self.dat.picks.samp1[-1, :])].astype(int)], color='m', picker=5)[0])
                self.tline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp1[-1, :])], self.yd[self.dat.picks.samp1[-1, :][~np.isnan(self.dat.picks.samp2[-1, :])].astype(int)], color='g')[0])
                self.bline.append(self.ax.plot(self.xd[~np.isnan(self.dat.picks.samp3[-1, :])], self.yd[self.dat.picks.samp3[-1, :][~np.isnan(self.dat.picks.samp3[-1, :])].astype(int)], color='g')[0])

            self.kpid = self.fig.canvas.mpl_connect('key_press_event', self.press)
            self.bpid = self.fig.canvas.mpl_connect('pick_event', self.click)

            #####
            # Connect some stuff after things are set up
            # Do this here so we don't unintentionally trigger things that are not initialized
            #####
            self.minSpinner.valueChanged.connect(self._lim_update)
            self.maxSpinner.valueChanged.connect(self._lim_update)
            self.FrequencySpin.valueChanged.connect(self._freq_update)
            self.modeButton.clicked.connect(self._mode_update)
            self.newpickButton.clicked.connect(self._add_pick)

            plt.show(self.fig)
        except KeyboardInterrupt:
            plt.close('all')

    #######
    # Handling of keypress events
    #######
    def _color_select(self, val):
        self.im.set_cmap(plt.cm.get_cmap(val))
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _lim_update(self, val):
        if self.maxSpinner.value() < self.minSpinner.value():
            self.maxSpinner.setValue(self.minSpinner.value() + 1)
        self.im.set_clim(vmin=self.minSpinner.value(), vmax=self.maxSpinner.value())
        self.lims[0] = self.minSpinner.value()
        self.lims[1] = self.maxSpinner.value()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _freq_update(self, val):
        self.dat.picks.pickparams.freq_update(val)
        self.freq = val

    def _mode_update(self):
        _translate = QtCore.QCoreApplication.translate
        if self.pick_mode == 'select':
            self.modeButton.setText(_translate('MainWindow', 'Edit Mode'))
            self.FigCanvasWidget.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
            self.pick_mode = 'edit'
            self.fig.canvas.mpl_disconnect(self.bpid)
            self.bpid = self.fig.canvas.mpl_connect('button_press_event', self.click)
        else:
            self.modeButton.setText(_translate('MainWindow', 'Select Mode'))
            self.FigCanvasWidget.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            self.pick_mode = 'select'
            self.fig.canvas.mpl_disconnect(self.bpid)
            self.bpid = self.fig.canvas.mpl_connect('pick_event', self.click)

    #######
    # Handling of mouse events
    #######
    def click(self, event):
        # This will handle both edit mode and select mode clicks
        if self.FigCanvasWidget.mpl_toolbar._active is not None:
            return
        if self.pick_mode == 'edit':
            if len(self.cline) == 0:
                self._add_pick()
            if event.button == 1:
                tnum, snum = np.argmin(np.abs(self.xd - event.xdata)), np.argmin(np.abs(self.yd - event.ydata))
                picks = picklib.pick(self.dat.data[:, self.dat.picks.lasttrace.tnum[self.current_layer]:tnum], self.dat.picks.lasttrace.snum[self.current_layer], snum, pickparams=self.dat.picks.pickparams)
                self.current_pick[:, self.dat.picks.lasttrace.tnum[self.current_layer]:tnum] = picks
                self.dat.picks.update_pick(self._pick_ind, self.current_pick)
                self.dat.picks.lasttrace.tnum[self.current_layer] = tnum
                self.dat.picks.lasttrace.snum[self.current_layer] = snum
                if self.cline[self._pick_ind] is None:
                    self.cline[self._pick_ind], = self.ax.plot(self.xd[~np.isnan(self.current_pick[1, :])], self.yd[self.current_pick[1, :][~np.isnan(self.current_pick[1, :])].astype(int)], color='g')
                    self.tline[self._pick_ind], = self.ax.plot(self.xd[~np.isnan(self.current_pick[0, :])], self.yd[self.current_pick[0, :][~np.isnan(self.current_pick[0, :])].astype(int)], color='m')
                    self.bline[self._pick_ind], = self.ax.plot(self.xd[~np.isnan(self.current_pick[2, :])], self.yd[self.current_pick[2, :][~np.isnan(self.current_pick[2, :])].astype(int)], color='m')
                else:
                    self.cline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[1, :])], self.yd[self.current_pick[1, :][~np.isnan(self.current_pick[1, :])].astype(int)])
                    self.tline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[0, :])], self.yd[self.current_pick[0, :][~np.isnan(self.current_pick[0, :])].astype(int)])
                    self.bline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[2, :])], self.yd[self.current_pick[2, :][~np.isnan(self.current_pick[2, :])].astype(int)])
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                self._saved = False

            elif event.button == 3:
                # Delete picks
                tnum, snum = np.argmin(np.abs(self.xd - event.xdata)), np.argmin(np.abs(self.yd - event.ydata))
                self.current_pick[:, tnum:] = np.nan
                self.cline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[1, :])], self.yd[self.current_pick[1, :][~np.isnan(self.current_pick[1, :])].astype(int)])
                self.tline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[0, :])], self.yd[self.current_pick[0, :][~np.isnan(self.current_pick[0, :])].astype(int)])
                self.bline[self._pick_ind].set_data(self.xd[~np.isnan(self.current_pick[2, :])], self.yd[self.current_pick[2, :][~np.isnan(self.current_pick[2, :])].astype(int)])
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                self._saved = False
        elif self.pick_mode == 'select':
            self.select_lines(event)

    def select_lines(self, event):
        thisline = event.artist
        if thisline in self.cline:
            self._pick_ind = self.cline.index(thisline)
            for c, b, t in zip(self.cline, self.bline, self.tline):
                if self._pick_ind == self.cline.index(thisline):
                    c.set_color('g')
                    b.set_color('m')
                    t.set_color('m')
                else:
                    c.set_color('b')
                    b.set_color('y')
                    t.set_color('y')

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _dat_to_snumtnum(self, x, y):
        if self.xscale == 'tnum':
            xo = int(x)
        else:
            xo = np.argmin(np.abs(self.dat.dist - x))

        yo = np.argmin(np.abs(getattr(self.dat, self.yscale) - y))
        return xo, yo

    #######
    # Logistics of saving and closing
    #######
    def closeEvent(self, event):
        if not self._saved:
            self._save_cancel_close(event)
        else:
            event.accept()

    def _save_cancel_close(self, event):
        dialog = QMessageBox()
        dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel)
        result = dialog.exec()
        if result == QMessageBox.Cancel:
            event.ignore()
        elif result == QMessageBox.Close:
            event.accept()
        else:
            if self.fn is None:
                if not self._save_as(event):
                    event.ignore() 
                else:
                    event.accept()
            else:
                self._save()
                event.accept()

    def _save_inplace(self, evt):
        """Save the file without changing name"""
        self_save_fn(self.dat.fn)

    def _save_pick(self, evt):
        """Save with _pick appended"""
        self._save_fn(self.dat.fn[:-4] + '_pick.mat')

    def _save_as(self, event=None):
        """Fancy file handler for gracious exit"""
        fn, test = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", self.dat.fn, "All Files (*);;mat Files (*.mat)")
        if fn:
            self._save_fn(fn)
        return fn

    def _save_fn(self, fn):
        self.fn = fn
        self.dat.save(fn)
        self._saved = True
        self.actionSave_pick.triggered.disconnect()
        self.actionSave_pick.triggered.connect(self._save_as)

    #######
    # Enable the key presses from the old stointerpret
    #######

    def press(self, event):
        if event.key == 'd':
            self.press_f()
        elif event.key == ' ':
            self.press_space()
        elif event.key == 'n':
            self.press_p()

    def _add_pick(self):
        # Give the user a visual clue to what is being picked by using different colors for the old lines
        # I think that c, b, t should always be the same length, if this doesnt work I think it means there is a deeper bug
        for cl, bl, tl in zip(self.cline, self.bline, self.tline):
            if cl is not None:
                cl.set_color('b')
                bl.set_color('y')
                tl.set_color('y')
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()

        self.cline.append(None)
        self.bline.append(None)
        self.tline.append(None)
        pick_ind = self.dat.picks.add_pick()
        self._pick_ind = pick_ind - 1
        d = np.zeros((5, self.dat.tnum))
        d[d == 0] = np.nan
        self.current_pick = d


# We want to add this fancy colormap
colorb = [(1.0000, 1.0000, 1.000),
          (0.9984, 1.0000, 0.2000),
          (1.0000, 0.6792, 0.6500),
          (0.5407, 0.9000, 0.5400),
          (0.7831, 0.8950, 0.8950),
          (1.0000, 1.0000, 1.0000),
          (0.3507, 0.3500, 0.7000),
          (0.1740, 0.5800, 0.5800),
          (0.0581, 0.5800, 0.0580),
          (0.4792, 0.4800, 0.0600),
          (0.8000, 0., 0.),
          (0., 0., 0.)]

percents = np.array([0, 63, 95, 114, 123, 127, 130, 134, 143, 162, 194, 256])
percents = percents / 256.

plt.cm.register_cmap(name='CEGSIC', cmap=colors.LinearSegmentedColormap.from_list('CEGSIC', list(zip(percents, colorb))))
