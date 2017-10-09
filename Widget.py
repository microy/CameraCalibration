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
import Calibration

# Main window
class CameraCalibrationWidget( QtWidgets.QWidget ) :
	# Signal sent to update the image in the widget
	update_image = QtCore.pyqtSignal()
	# Initialization
	def __init__( self, parent = None ) :
		# Initialise QWidget
		super( CameraCalibrationWidget, self ).__init__( parent )
		# Set the window title
		self.setWindowTitle( 'Camera Calibration' )
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
		# Connect the signal to update the image
		self.update_image.connect( self.UpdateImage )
		# Initialize the camera
		self.camera = Camera.UsbCamera()
		# Fix the widget size
		self.image_widget.setFixedSize( self.camera.width, self.camera.height )
		# Create a QImage to store and display the image from the camera
		self.qimage = QtGui.QImage( self.camera.width, self.camera.height, QtGui.QImage.Format_RGB888 )
		# Widget to display the chessboard on the image
		self.chessboard_preview = ChessboardPreview( self, self.camera.width, self.camera.height )
		# Start image acquisition
		self.camera.StartCapture(  self.ImageCallback  )
	# A new image is sent by the camera
	def ImageCallback( self ) :
		# Copy the camera image
		self.image = np.copy( self.camera.image )
		# Display the image
		self.update_image.emit()
		# Preview the calibration chessboard on the image
		if self.button_chessboard.isChecked() :
			self.chessboard_preview.update_image.emit()
	# Process and display the given image
	def UpdateImage( self ) :
		# Convert image color format from BGR to RGB
		image = cv2.cvtColor( self.image, cv2.COLOR_BGR2RGB )
		# Get the pointer of the Qt image data
		qimage_pointer = self.qimage.bits()
		qimage_pointer.setsize( image.size )
		# Copy the camera image in the Qt image
		qimage_pointer[ 0 : image.size ] = image[ 0 : image.size ]
		# Set the image to the Qt widget
		self.image_widget.setPixmap( QtGui.QPixmap.fromImage( self.qimage ) )
		# Update the widget
		self.image_widget.update()
	# Camera calibration
	def Calibration( self ) :
		# Calibrate the camera
		calibration_successful = Calibration.CameraCalibration()
		# Calibration done
		if calibration_successful : QtWidgets.QMessageBox.information( self, "Camera calibration", "Camera calibration done !" )
		# Calibration failed
		else : QtWidgets.QMessageBox.warning( self, "Camera calibration", "Camera calibration failed !" )
	# Toggle the chessboard preview
	def ToggleChessboard( self ) :
		if self.button_chessboard.isChecked() : self.chessboard_preview.show()
		else : self.chessboard_preview.hide()
	# Save the image
	def Capture( self ) :
		current_time = time.strftime( '%Y%m%d_%H%M%S' )
		print( 'Save images {} to disk...'.format( current_time ) )
		cv2.imwrite( 'camera-{}.png'.format( current_time ), self.image )
	# Update the calibration pattern size
	def UpdatePatternSize( self, _ ) :
		Calibration.pattern_size = ( self.spinbox_pattern_rows.value(), self.spinbox_pattern_cols.value() )
	# Close the widget
	def closeEvent( self, event ) :
		# Stop image acquisition
		self.camera.StopCapture()
		# Close the chessboard preview window
		self.chessboard_preview.close()
		# Close main application
		event.accept()

# Chessboard preview window
class ChessboardPreview( QtWidgets.QLabel ) :
	# Signal sent to update the image in the widget
	update_image = QtCore.pyqtSignal()
	# Initialization
	def __init__( self, parent, width, height ) :
		# Initialise QLabel
		super( ChessboardPreview, self ).__init__()
		# Register the main window
		self.parent = parent
		# Set the window title
		self.setWindowTitle( 'Chessboard detection preview' )
		# Connect the signal to update the image
		self.update_image.connect( self.UpdateImage )
		# Set the widget size
		self.setScaledContents( True )
		self.setFixedSize( width, height )
		# Create a QImage to store and display the image from the camera
		self.qimage = QtGui.QImage( width, height, QtGui.QImage.Format_RGB888 )
		# Set the Escape key to close the application
		QtWidgets.QShortcut( QtGui.QKeySequence( QtCore.Qt.Key_Escape ), self ).activated.connect( self.close )
	# Detect the chessboard on the image and display the result
	def UpdateImage( self ) :
		# Preview the calibration chessboard on the image
		image = Calibration.PreviewChessboard( np.copy(self.parent.image) )
		# Convert image color format from BGR to RGB
		image = cv2.cvtColor( image, cv2.COLOR_BGR2RGB )
		# Get the pointer of the Qt image data
		qimage_pointer = self.qimage.bits()
		qimage_pointer.setsize( image.size )
		# Copy the camera image in the Qt image
		qimage_pointer[ 0 : image.size ] = image[ 0 : image.size ]
		# Set the image to the Qt widget
		self.setPixmap( QtGui.QPixmap.fromImage( self.qimage ) )
		# Update the widget
		self.update()
	# Close the widget
	def closeEvent( self, event ) :
		# Tell the parent this window is closed
		self.parent.button_chessboard.setChecked( False )
		# Close main application
		event.accept()
