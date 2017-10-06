# -*- coding:utf-8 -*-

#
# Module to capture images from USB camera
#

# External dependencies
import threading
import cv2

# Thread to read the images from a USB camera
class UsbCamera( threading.Thread ) :
	# Initialisation
	def __init__( self ) :
		# Initialize the thread
		super( UsbCamera, self ).__init__()
		# Initialize the camera
		self.camera = cv2.VideoCapture( 0 )
	# Return the image width
	@property
	def width( self ) :
		return self.camera.get( cv2.CAP_PROP_FRAME_WIDTH )
	# Return the image height
	@property
	def height( self ) :
		return self.camera.get( cv2.CAP_PROP_FRAME_HEIGHT )
	# Start acquisition
	def StartCapture( self, image_callback ) :
		# Function called when the image is ready
		self.image_callback = image_callback
		# Start the capture loop
		self.running = True
		self.start()
	# Stop acquisition
	def StopCapture( self ) :
		self.running = False
		self.join()
	# Thread main loop
	def run( self ) :
		# Thread running
		while self.running :
			# Capture image
			_, self.image = self.camera.read()
			# Send the image via the external callback function
			self.image_callback()
		# Release the cameras
		self.camera.release()
