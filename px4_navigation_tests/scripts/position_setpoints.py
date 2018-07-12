#!/usr/bin/env python

import rospy # ROS interface
import pymap3d as pm # coordinate conversion

from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import Point, PoseStamped
from mavros_msgs.msg import *
from mavros_msgs.srv import *

class Controller:

	def __init__(self):

		# Current GPS Coordinates
		self.current_lat					= 0.0
		self.current_lon					= 0.0
		self.current_alt					= 0.0

		# home GPS Coordinates
		self.home_lat					= 0.0
		self.home_lon					= 0.0
		self.home_alt					= 0.0
		self.receivedHomeGPS  = False

		# Current local ENU coordinates
		self.current_local_x				= 0.0
		self.current_local_y				= 0.0
		self.current_local_z				= 0.0


		# Instantiate a setpoint topic structure
		self.mavros_sp					= PositionTarget()
		# use position setpoints
		self.mavros_sp.type_mask		= int('101111111000', 2)
		# FRAME_LOCAL_NED
		self.mavros_sp.coordinate_frame = 1

		######### Callbacks #########

	def gpsCb(self, msg):
		if msg is not None:
			self.current_lat = msg.latitude
			self.current_lon = msg.longitude
			self.current_alt = msg.altitude
     


	def localPoseCb(self, msg):
		if msg is not None:
			self.current_local_x = msg.pose.position.x
			self.current_local_y = msg.pose.position.y
			self.current_local_z = msg.pose.position.z

	def homeCb(self, msg):
		if msg is not None:
			self.home_lat = msg.geo.latitude
			self.home_lon = msg.geo.longitude
			self.home_alt = msg.geo.altitude
			self.receivedHomeGPS = True

    

	def gpsSpCb(self, msg):
		# lat = msg.x; lon = msg.y;
		# msg.z is the altitude setpoint in ENU
		if msg is not None:
			target_lat = msg.x
			target_lon = msg.y
			target_alt = msg.z # in ENU

			target_gps_alt = self.current_alt
			delta_x, delta_y, delta_z = pm.geodetic2enu(target_lat, target_lon, target_gps_alt, self.home_lat, self.home_lon, self.home_alt)

			#self.mavros_sp.position.x = self.current_local_x + delta_x
			#self.mavros_sp.position.y = self.current_local_y + delta_y
			self.mavros_sp.position.x = delta_x
			self.mavros_sp.position.y = delta_y
			self.mavros_sp.position.z = target_alt

                        print "hello"

	def positionSpCb(self, msg):
		if msg is not None:
			self.mavros_sp.position.x =  msg.x #self.current_local_x+5*msg.x
			self.mavros_sp.position.y =  msg.y #self.current_local_y+5*msg.y
			self.mavros_sp.position.z = msg.z
                        print "x : ",self.current_local_x
                        print "y : ",self.current_local_y
			self.receivedHomeGPS = True 


def main():
	rospy.init_node('gps_setpoint_node', anonymous=True)

	rospy.logwarn("GPS setpoints node is started")

	K = Controller()

	########## Subscribers ##########

	# Subscriber: GPS
	rospy.Subscriber("mavros/global_position/raw/fix", NavSatFix, K.gpsCb)

	# Subscriber: Local pose
	rospy.Subscriber("mavros/local_position/pose", PoseStamped, K.localPoseCb)

	# User GPS setpoint
	rospy.Subscriber("gps_setpoint", Point, K.gpsSpCb)

        # subscriber to home topic
        rospy.Subscriber("mavros/home_position/home", HomePosition, K.homeCb)

        # subscriber to relative position setpoint
        rospy.Subscriber("relative_position_setpoint", Point, K.positionSpCb)

	########## Publishers ##########

	# Publisher: PositionTarget
	setp_pub = rospy.Publisher("mavros/setpoint_raw/local", PositionTarget, queue_size=1)

	rate = rospy.Rate(10.0)

	i = 0
	while not rospy.is_shutdown() and not K.receivedHomeGPS:
		# Initialize setpoint
		K.mavros_sp.position.x = K.current_local_x
		K.mavros_sp.position.y = K.current_local_y
		K.mavros_sp.position.z = 3.0

		i = i +1
		rate.sleep()

	while not rospy.is_shutdown():

		setp_pub.publish(K.mavros_sp)

		rate.sleep()

if __name__ == '__main__':
	try:
		main()
	except rospy.ROSInterruptException:
		pass
