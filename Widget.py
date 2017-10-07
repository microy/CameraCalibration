#! /usr/bin/env python
# -*- coding:utf-8 -*-

#
# Camera calibration application
#

# External dependencies
import time
import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import Camera
from Camera import UsbCamera
import Calibration


# User interface
class CameraCalibrationWidget( QtWidgets.QWidget ) :
	# Signal sent to update the image in the widget
	update_image = QtCore.pyqtSignal()
	# Initialization
	def __init__( self, parent = None ) :
		# Initialise QWidget
		super( CameraCalibrationWidget, self ).__init__( parent )
		# Set the window title
		self.setWindowTitle( 'Camera Calibration' )
		# Initialize the viewing parameters
		self.chessboard_enabled = False
		# Connect the signal to update the image
		self.update_image.connect( self.UpdateImage )
		# Widget to display the image from the camera
		self.image_widget = QtWidgets.QLabel( self )
		self.image_widget.setScaledContents( True )
		# Widget elements
		self.button_chessboard = QtWidgets.QPushButton( 'Chessboard', self )
		self.button_chessboard.setCheckable( True )
		self.button_chessboard.setShortcut( 'F1' )
		self.button_chessboard.clicked.connect( self.ToggleChessboard )
		self.button_capture = QtWidgets.QPushButton( 'Capture', self )
		self.button_capture.setShortcut( 'Space' )
		self.button_capture.clicked.connect( self.Capture )
		self.button_calibration = QtWidgets.QPushButton( 'Calibration', self )
		self.button_calibration.setShortcut( 'F2' )
		self.button_calibration.clicked.connect( self.Calibration )
		self.spinbox_pattern_rows = QtWidgets.QSpinBox( self )
		self.spinbox_pattern_rows.setValue( Calibration.pattern_size[0] )
		self.spinbox_pattern_rows.valueChanged.connect( self.UpdatePatternSize )
		self.spinbox_pattern_cols = QtWidgets.QSpinBox( self )
		self.spinbox_pattern_cols.setValue( Calibration.pattern_size[1] )
		self.spinbox_pattern_cols.valueChanged.connect( self.UpdatePatternSize )
		# Widget layout
		self.layout_pattern_size = QtWidgets.QHBoxLayout()
		self.layout_pattern_size.addWidget( QtWidgets.QLabel( 'Pattern size :' ) )
		self.layout_pattern_size.addWidget( self.spinbox_pattern_rows )
		self.layout_pattern_size.addWidget( self.spinbox_pattern_cols )
		self.layout_controls = QtWidgets.QHBoxLayout()
		self.layout_controls.addWidget( self.button_chessboard )
		self.layout_controls.addWidget( self.button_capture )
		self.layout_controls.addWidget( self.button_calibration )
		self.layout_controls.addLayout( self.layout_pattern_size )
		self.layout_global = QtWidgets.QVBoxLayout( self )
		self.layout_global.addWidget( self.image_widget )
		self.layout_global.addLayout( self.layout_controls )
		self.layout_global.setSizeConstraint( QtWidgets.QLayout.SetFixedSize )
		# Set the Escape key to close the application
		QtWidgets.QShortcut( QtGui.QKeySequence( QtCore.Qt.Key_Escape ), self ).activated.connect( self.close )
		# Initialize the camera
		self.camera = UsbCamera()
		# Fix the widget size
		self.image_widget.setFixedSize( self.camera.width, self.camera.height )
		# Start image acquisition
		self.camera.StartCapture(  self.ImageCallback  )
	# A new image is sent by the camera
	def ImageCallback( self ) :
		# Copy the camera image
		self.image = np.copy( self.camera.image )
		# Process the image
		self.update_image.emit()
	# Process and display the given image
	def UpdateImage( self ) :
		# Copy images for display
		image_displayed = np.copy( self.image )
		# Preview the calibration chessboard on the image
		if self.chessboard_enabled :
			image_displayed = Calibration.PreviewChessboard( image_displayed )
		# Convert image color format from BGR to RGB
		image_displayed = cv2.cvtColor( image_displayed, cv2.COLOR_BGR2RGB )
		# Create a Qt image
		qimage = QtGui.QImage( image_displayed, image_displayed.shape[1], image_displayed.shape[0], QtGui.QImage.Format_RGB888 )
		# Set the image to the Qt widget
		self.image_widget.setPixmap( QtGui.QPixmap.fromImage( qimage ) )
		# Update the widget
		self.image_widget.update()
	# Toggle the chessboard preview
	def ToggleChessboard( self ) :
		self.chessboard_enabled = not self.chessboard_enabled
	# Save the image
	def Capture( self ) :
		current_time = time.strftime( '%Y%m%d_%H%M%S' )
		print( 'Save images {} to disk...'.format( current_time ) )
		cv2.imwrite( 'camera-{}.png'.format( current_time ), self.image )
	# Camera calibration
	def Calibration( self ) :
		try :
			Calibration.CameraCalibration()
			print( 'Calibration done.' )
		except :
			print( 'Calibration failed...' )
	# Update the calibration pattern size
	def UpdatePatternSize( self, _ ) :
		Calibration.pattern_size = ( self.spinbox_pattern_rows.value(), self.spinbox_pattern_cols.value() )
	# Close the widget
	def closeEvent( self, event ) :
		# Stop image acquisition
		self.camera.StopCapture()
		# Close main application
		event.accept()
