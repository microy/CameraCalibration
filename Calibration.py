# -*- coding:utf-8 -*-

#
# Camera calibration module
#

# External dependencies
import glob
import math
import pickle
import threading
import cv2
import numpy as np

# Calibration pattern size
pattern_size = ( 9, 6 )

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

# Thread to calibrate the camera
class CalibrationThread( threading.Thread ) :
	# Initialisation
	def __init__( self, calibration_done_callback ) :
		# Initialize the thread
		super( CalibrationThread, self ).__init__()
		# Register the parent callback function
		self.calibration_done = calibration_done_callback
	# Thread main loop
	def run( self ) :
		try :
			# Calibrate the camera
			CameraCalibration()
		except :
			# Tell the parent the calibration has failed
			self.calibration_done( False )
		else :
			# Tell the parent the calibration is done
			self.calibration_done( True )

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
