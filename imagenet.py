#!/usr/bin/python3

#Source https://github.com/dusty-nv/jetson-inference/blob/master/python/examples/imagenet.py
import jetson.inference
import jetson.utils
import argparse
import sys
import time
from datetime import datetime
import os
from os import popen
import json
import subprocess


def iot_message(bus_number,date,time_in_sec):
	#send variables as an argument to iot_http.py to publish it to Pub/Sub
	a_list = [bus_number,date,time_in_sec]
	message = ",".join(a_list) # join text so there is no spaces in between variables
	command = (['python3', 'path_here/iot_http.py', '--message', message])
	subprocess.Popen(command, shell=False, stderr=None, stdout=None, stdin=None)

def log_time_ariv(event_time):
	#log data to csv for returning bus
	global j
	h, m, s = event_time.split(':')
	time_in_sec = str((int(h) * 3600 + int(m) * 60 + int(s)) - 32400)
	j = j + 1
	date = datetime.today().date()
	bus_number = "bus_" + str(j)
	data = [bus_number,date,time_in_sec]
	date = str(date)
	time_in_sec = str(time_in_sec)
	with open('path_here/arriving_bus.csv', 'a',newline='') as f:
		for line in data:
			f.write(f"{line},")
		f.write(f"\n")
	iot_message(bus_number,date,time_in_sec)

def log_time_depart(event_time):
	#log data to csv for returning bus
	global i
	h, m, s = event_time.split(':')
	time_in_sec = str((int(h) * 3600 + int(m) * 60 + int(s)) - 32400)
	i = i + 1
	date = datetime.today().date()
	bus_number = "bus_" + str(i)
	data = [bus_number,date,time_in_sec]
	print(time_in_sec)
	with open('path_here/departing_bus.csv', 'a',newline='') as f:
		for line in data:
			f.write(f"{line},")
		f.write(f"\n")


# parse the command line
parser = argparse.ArgumentParser(description="Classify a live camera stream using an image recognition DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.imageNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="path_here", nargs='?', help="URI of the output stream")
parser.add_argument("output_BUS_URI", type=str, default="path_here", nargs='?', help="URI of the output stream")
parser.add_argument("output_DEP_BUS_URI", type=str, default="path_here", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="googlenet", help="pre-trained model to load (see below for options)")
parser.add_argument("--camera", type=str, default="0", help="index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.")
parser.add_argument("--width", type=int, default=1280, help="desired width of camera stream (default is 1280 pixels)")
parser.add_argument("--height", type=int, default=720, help="desired height of camera stream (default is 720 pixels)")
parser.add_argument('--headless', action='store_true', default=(), help="run without display")

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)


# load the recognition network
net = jetson.inference.imageNet(opt.network, sys.argv)
#time
timestr = time.strftime("%Y%m%d-%H%M%S")
# create video sources & outputs
input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)
output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv)
output_bus = jetson.utils.videoOutput(opt.output_BUS_URI, argv=sys.argv)
output_dep_bus = jetson.utils.videoOutput(opt.output_DEP_BUS_URI, argv=sys.argv)
font = jetson.utils.cudaFont()
number = 0
bus_number = 0
dep_bus_number = 0
bus_confidence = 0
i = 0
j = 0
depart_bus = False
arrive_bus = False

	 
	# process frames until the user exits
while True:
	# capture the next image
	img = input.Capture()

	# classify the image
	class_id, confidence = net.Classify(img)

	# find the object description
	class_desc = net.GetClassDesc(class_id)

	#saving bck photos
	if (0.5 < confidence < 0.55 and class_desc == "background"):
		number = number + 1
		if number == 1000:
			font = jetson.utils.cudaFont(size=15)	
			font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 10, 10, font.White, font.Gray10)
			output.Render(img)
			number = 0

	#saving bus photos adn arrival time
	if (confidence > 0.92 and class_desc == "arriving_bus"):
		bus_number = bus_number + 1		
		if bus_number == 15:
			font = jetson.utils.cudaFont(size=15)	
			font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 10, 10, font.White, font.Gray10)

			
			now = datetime.now()
			if arrive_bus == False:
				latesta_time = now
				str_time = now.strftime("%H:%M:%S")
				log_time_ariv(str_time)
				arrive_bus = True
				output_bus.Render(img)
			elif (arrive_bus == True and  (now - latesta_time).total_seconds() > 70 ):
				str_time = now.strftime("%H:%M:%S")
				log_time_ariv(str_time)
				latesta_time = now
				output_bus.Render(img)
			bus_number = 0
	
	#saving bus photos adn arrival time
	if (confidence > 0.92 and class_desc == "departing_bus"):
		dep_bus_number = dep_bus_number + 1		
		if dep_bus_number == 17:
			font = jetson.utils.cudaFont(size=15)	
			font.OverlayText(img, img.width, img.height, "{:05.2f}% {:s}".format(confidence * 100, class_desc), 10, 10, font.White, font.Gray10)
			
			now = datetime.now()
			if depart_bus == False:
				latestd_time = now
				str_time = now.strftime("%H:%M:%S")
				log_time_depart(str_time)
				depart_bus = True
				output_dep_bus.Render(img)
			elif (depart_bus == True and  (now - latestd_time).total_seconds() > 70 ):
				str_time = now.strftime("%H:%M:%S")
				log_time_depart(str_time)
				latestd_time = now
				output_dep_bus.Render(img)
			dep_bus_number = 0

	# update the title bar
	output.SetStatus("{:s} | Network {:.0f} FPS".format(net.GetNetworkName(), net.GetNetworkFPS()))

	# print out performance info
	net.PrintProfilerTimes()

	# exit on input/output EOS
	if not input.IsStreaming() or not output.IsStreaming():
		break