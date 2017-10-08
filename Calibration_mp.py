# -*- coding:utf-8 -*-

#
# Camera calibration module
#

# External dependencies
import glob
import math
import multiprocessing
import pickle
import cv2
import numpy as np

# Calibration pattern size
pattern_size = ( 9, 6 )

# Chessboard detection flags
chessboard_flags  = 0
chessboard_flags |= cv2.CALIB_CB_ADAPTIVE_THRESH
chessboard_flags |= cv2.CALIB_CB_NORMALIZE_IMAGE

# Camera calibration flags
calibration_flags  = 0
#calibration_flags |= cv2.CALIB_USE_INTRINSIC_GUESS
#calibration_flags |= cv2.CALIB_FIX_PRINCIPAL_POINT
#calibration_flags |= cv2.CALIB_FIX_ASPECT_RATIO
#calibration_flags |= cv2.CALIB_ZERO_TANGENT_DIST
calibration_flags |= cv2.CALIB_RATIONAL_MODEL
#calibration_flags |= cv2.CALIB_FIX_K3
calibration_flags |= cv2.CALIB_FIX_K4
calibration_flags |= cv2.CALIB_FIX_K5

# Find the chessboard quickly, and draw it
def PreviewChessboard( image ) :
	# Convert image from BGR to Grayscale
	grayscale_image = cv2.cvtColor( image, cv2.COLOR_BGR2GRAY )
	# Find the chessboard corners on the image
	found, corners = cv2.findChessboardCorners( grayscale_image, pattern_size, flags = cv2.CALIB_CB_FAST_CHECK )
	# Draw the chessboard corners on the image
	if found : cv2.drawChessboardCorners( image, pattern_size, corners, found )
	# Return the image with the chessboard if found
	return image

# Find the chessboard in an image file
def ChessboardDetection( filename ) :
	# 2D points
	img_points = []
	# Load the image
	image = cv2.imread( filename, cv2.IMREAD_GRAYSCALE )
	# Find the chessboard corners on the image
	found, corners = cv2.findChessboardCorners( image, pattern_size, flags=chessboard_flags )
	# Pattern not found
	if found :
		# Termination criteria
		criteria = ( cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 30, 1e-5 )
		# Refine the corner positions
		cv2.cornerSubPix( image, corners, (11, 11), (-1, -1), criteria )
		# Store image and corner informations
		img_points.append( corners.reshape(-1, 2) )
	else : print( 'Pattern not found on image {}...'.format( filename ) )
	return [ filename, img_points ]

# Camera calibration
def CameraCalibration() :
	# Calibration image files
	image_files = sorted( glob.glob( 'camera-*.png' ) )
	# Start chessboard detection processes
	with multiprocessing.Pool() as pool :
		result = pool.map( ChessboardDetection, image_files )
	# Images with chessboard found
	img_files = [ x[0] for x in result if x[1] ]
	# 2D points
	img_points = [ x[1] for x in result if x[1] ]
	# Abort if no chessboard has been found
	if not img_files :
		print( 'Camera calibration aborted. No chessboard found...' )
		return False
	# Get image size
	height, width = cv2.imread( image_files[0] ).shape[:2]
	img_size = ( width, height )
	# Chessboard pattern
	pattern_points = np.zeros( (np.prod(pattern_size), 3), np.float32 )
	pattern_points[:,:2] = np.indices(pattern_size).T.reshape(-1, 2)
	# 3D points
	obj_points = [ pattern_points for _ in range(len(img_files)) ]
	# Camera calibration
	calibration = cv2.calibrateCamera( obj_points, img_points, img_size, None, None, flags=calibration_flags )
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
	# Camera calibration successful
	return True



# Main application
if __name__ == '__main__' :
	import timeit
	print('multiprocessing')
	print( timeit.timeit("Calibration_mp.CameraCalibration()", setup="import Calibration_mp", number=1) )
	print('monoprocessing')
	print( timeit.timeit("Calibration.CameraCalibration()", setup="import Calibration", number=1) )
