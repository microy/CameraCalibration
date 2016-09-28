#! /usr/bin/env python
# -*- coding:utf-8 -*-

#
# Camera calibration application
#

# External dependencies
import glob
import math
import pickle
import sys
import time
import cv2
import numpy as np
from PyQt4 import QtCore
from PyQt4 import QtGui
from Camera import UsbCamera


# Calibration pattern size
pattern_size = ( 9, 6 )


# User interface
class CameraCalibrationWidget( QtGui.QWidget ) :
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
		self.image_widget = QtGui.QLabel( self )
		self.image_widget.setScaledContents( True )
		# Widget elements
		self.button_chessboard = QtGui.QPushButton( 'Chessboard', self )
		self.button_chessboard.setCheckable( True )
		self.button_chessboard.setShortcut( 'F1' )
		self.button_chessboard.clicked.connect( self.ToggleChessboard )
		self.button_capture = QtGui.QPushButton( 'Capture', self )
		self.button_capture.setShortcut( 'Space' )
		self.button_capture.clicked.connect( self.Capture )
		self.button_calibration = QtGui.QPushButton( 'Calibration', self )
		self.button_calibration.setShortcut( 'F2' )
		self.button_calibration.clicked.connect( self.Calibration )
		self.spinbox_pattern_rows = QtGui.QSpinBox( self )
		self.spinbox_pattern_rows.setValue( pattern_size[0] )
		self.spinbox_pattern_rows.valueChanged.connect( self.UpdatePatternSize )
		self.spinbox_pattern_cols = QtGui.QSpinBox( self )
		self.spinbox_pattern_cols.setValue( pattern_size[1] )
		self.spinbox_pattern_cols.valueChanged.connect( self.UpdatePatternSize )
		# Widget layout
		self.layout_pattern_size = QtGui.QHBoxLayout()
		self.layout_pattern_size.addWidget( QtGui.QLabel( 'Pattern size :' ) )
		self.layout_pattern_size.addWidget( self.spinbox_pattern_rows )
		self.layout_pattern_size.addWidget( self.spinbox_pattern_cols )
		self.layout_controls = QtGui.QHBoxLayout()
		self.layout_controls.addWidget( self.button_chessboard )
		self.layout_controls.addWidget( self.button_capture )
		self.layout_controls.addWidget( self.button_calibration )
		self.layout_controls.addLayout( self.layout_pattern_size )
		self.layout_global = QtGui.QVBoxLayout( self )
		self.layout_global.addWidget( self.image_widget )
		self.layout_global.addLayout( self.layout_controls )
		self.layout_global.setSizeConstraint( QtGui.QLayout.SetFixedSize )
		# Set the Escape key to close the application
		QtGui.QShortcut( QtGui.QKeySequence( QtCore.Qt.Key_Escape ), self ).activated.connect( self.close )
		# Initialize the camera
		self.camera = UsbCamera()
		# Fix the widget size
		self.image_widget.setFixedSize( self.camera.width, self.camera.height )
		# Start image acquisition
		self.camera.StartCapture(  self.ImageCallback  )
	# Receive the frame sent by the camera
	def ImageCallback( self, image ) :
		# Get the image
		self.image = image
		# Process the image
		self.update_image.emit()
	# Process and display the given image
	def UpdateImage( self ) :
		# Copy images for display
		image_displayed = np.copy( self.image )
		# Preview the calibration chessboard on the image
		if self.chessboard_enabled :
			image_displayed = PreviewChessboard( image_displayed )
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
		self.calibration = CameraCalibration()
		print( 'Calibration done.')
	# Update the calibration pattern size
	def UpdatePatternSize( self, _ ) :
		global pattern_size
		pattern_size = ( self.spinbox_pattern_rows.value(), self.spinbox_pattern_cols.value() )
	# Close the widget
	def closeEvent( self, event ) :
		# Stop image acquisition
		self.camera.StopCapture()
		# Close main application
		event.accept()


# Find the chessboard quickly, and draw it
def PreviewChessboard( image ) :
	# Convert image from BGR to Grayscale
	grayscale_image = cv2.cvtColor( image, cv2.COLOR_BGR2GRAY )
	# Find the chessboard corners on the image
	found, corners = cv2.findChessboardCorners( grayscale_image, pattern_size, flags = cv2.CALIB_CB_FAST_CHECK )
#	found, corners = cv2.findCirclesGrid( grayscale_image, pattern_size, flags = cv2.CALIB_CB_ASYMMETRIC_GRID )
	# Draw the chessboard corners on the image
	if found : cv2.drawChessboardCorners( image, pattern_size, corners, found )
	# Return the image with the chessboard if found
	return image


# Camera calibration
def CameraCalibration() :
	# Calibration image files
	image_files = sorted( glob.glob( 'camera-*.png' ) )
	# Chessboard pattern
	pattern_points = np.zeros( (np.prod(pattern_size), 3), np.float32 )
	pattern_points[:,:2] = np.indices(pattern_size).T.reshape(-1, 2)
	# Asymetric circles grid pattern
#	pattern_points = []
#	for i in xrange( pattern_size[1] ) :
#		for j in xrange( pattern_size[0] ) :
#			pattern_points.append( [ (2*j) + i%2 , i, 0 ] )
#	pattern_points = np.asarray( pattern_points, dtype=np.float32 )
	# Get image size
	height, width = cv2.imread( image_files[0] ).shape[:2]
#	img_size = tuple( cv2.pyrDown( cv2.imread( image_files[0] ), cv2.CV_LOAD_IMAGE_GRAYSCALE ).shape[:2] )
	img_size = ( width, height )
	# 3D points
	obj_points = []
	# 2D points
	img_points = []
	# Images with chessboard found
	img_files = []
	# For each image
	for filename in image_files :
		# Load the image
		image = cv2.imread( filename, cv2.IMREAD_GRAYSCALE )
		# Resize image
	#	image_small = cv2.resize( image, None, fx=image_scale, fy=image_scale )
	#	image_small = cv2.pyrDown( image )
	#	image = image_small
		image_small = image
		# Chessboard detection flags
		flags  = 0
		flags |= cv2.CALIB_CB_ADAPTIVE_THRESH
		flags |= cv2.CALIB_CB_NORMALIZE_IMAGE
		# Find the chessboard corners on the image
		found, corners = cv2.findChessboardCorners( image_small, pattern_size, flags=flags )
	#	found, corners = cv2.findCirclesGrid( image, pattern_size, flags = cv2.CALIB_CB_ASYMMETRIC_GRID )
		# Pattern not found
		if not found :
			print( 'Pattern not found on image {}...'.format( filename ) )
			continue
		# Rescale the corner position
	#	corners *= 1.0 / image_scale
	#	corners *= 2.0
		# Termination criteria
		criteria = ( cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 1e-5 )
		# Refine the corner positions
		cv2.cornerSubPix( image, corners, (11, 11), (-1, -1), criteria )
		# Store image and corner informations
		img_points.append( corners.reshape(-1, 2) )
		obj_points.append( pattern_points )
		img_files.append( filename )
	# Camera calibration flags
	flags  = 0
#	flags |= cv2.CALIB_USE_INTRINSIC_GUESS
#	flags |= cv2.CALIB_FIX_PRINCIPAL_POINT
#	flags |= cv2.CALIB_FIX_ASPECT_RATIO
#	flags |= cv2.CALIB_ZERO_TANGENT_DIST
	flags |= cv2.CALIB_RATIONAL_MODEL
#	flags |= cv2.CALIB_FIX_K3
	flags |= cv2.CALIB_FIX_K4
	flags |= cv2.CALIB_FIX_K5
	# Camera calibration
	calibration = cv2.calibrateCamera( obj_points, img_points, img_size, None, None, flags=flags )
	# Store the calibration results in a dictionary
	parameter_names = ( 'calib_error', 'camera_matrix', 'dist_coefs', 'rvecs', 'tvecs' )
	calibration = dict( zip( parameter_names, calibration ) )
	# Compute reprojection error
	calibration['reproject_error'] = 0
	for i, obj in enumerate( obj_points ) :
		# Reproject the object points using the camera parameters
		reprojected_img_points, _ = cv2.projectPoints( obj, calibration['rvecs'][i],
		calibration['tvecs'][i], calibration['camera_matrix'], calibration['dist_coefs'] )
		# Compute the error with the original image points
		error = cv2.norm( img_points[i], reprojected_img_points.reshape(-1, 2), cv2.NORM_L2 )
		# Add to the total error
		calibration['reproject_error'] += error * error
	calibration['reproject_error'] = math.sqrt( calibration['reproject_error'] / (len(obj_points) * np.prod(pattern_size)) )
	# Backup calibration parameters for future use
	calibration['img_points'] = img_points
	calibration['obj_points'] = obj_points
	calibration['img_size'] = img_size
	calibration['img_files'] = img_files
	calibration['pattern_size'] = pattern_size
	# Write calibration results
	with open( 'calibration.log', 'w') as output_file :
		output_file.write( '\n~~~ Camera calibration ~~~\n\n' )
		output_file.write( 'Calibration error : {}\n'.format( calibration['calib_error'] ) )
		output_file.write( 'Reprojection error : {}\n'.format( calibration['reproject_error'] ) )
		output_file.write( 'Camera matrix :\n{}\n'.format( calibration['camera_matrix'] ) )
		output_file.write( 'Distortion coefficients :\n{}\n'.format( calibration['dist_coefs'].ravel() ) )
	# Write the calibration object with all the parameters
	with open( 'calibration.pkl' , 'wb') as output_file :
		pickle.dump( calibration, output_file, pickle.HIGHEST_PROTOCOL )


# Main application
if __name__ == '__main__' :
	application = QtGui.QApplication( sys.argv )
	widget = CameraCalibrationWidget()
	widget.show()
	sys.exit( application.exec_() )
