#! /usr/bin/env python
# -*- coding:utf-8 -*-

#
# Camera calibration application
#

# External dependencies
import sys
from PyQt5 import QtWidgets
import Widget


# Main application
if __name__ == '__main__' :
	application = QtWidgets.QApplication( sys.argv )
	widget = Widget.CameraCalibrationWidget()
	widget.show()
	sys.exit( application.exec_() )
