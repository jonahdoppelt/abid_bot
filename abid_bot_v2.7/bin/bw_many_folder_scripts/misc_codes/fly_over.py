#Created by Brian Taylor

#This script runs the movie once you have created all the necessary xml files
#It's still being writen, obviously.

#Source("/home/projects/bhbh_mag_inspiral_extras/many_folders_code/run_movie.py")

#Run with something like visit -cli -nowin -s run_movie.py "h5dir" "extrasDir" "bhdir" "savefolder"

import random
import csv
import sys
import time
import RotationMatrix as RM

from os import listdir, rename
from os.path import isfile, join
from fnmatch import fnmatch
from math import pi, sin, cos, tan, atan2, sqrt
sys.path.append("../../..")
from runModule import *

###############################################################################
#search for all the necessary data (preprocessing)
###############################################################################

PlotDens = 1 # Plot density
PlotVel  = 0 # Plot velocity arrows
PlotBsq2r= 0 # Plot B squared over 2 rho
cutPlot  = 0 #only show back half (y>0), needs view like: (0,-x,y)
Factor = 0.4 #See TODO for more info
print(sys.argv)

rank = int(sys.argv[6])
total_ranks = int(sys.argv[7])
tot_frames = int(sys.argv[8])
saveFolder=sys.argv[9]
root_dir = sys.argv[10]
h5dir = sys.argv[11]
extrasDir = sys.argv[12] 
streamXML = sys.argv[13]
vectorXML = sys.argv[14]
bsq2rXML = sys.argv[15]
max_density = sys.argv[16]
index = int(sys.argv[17])

frame_start = int(round((float(rank)/total_ranks)*tot_frames))
frame_end = int(round(((rank+1.0)/total_ranks)*tot_frames))

saveFolder = saveFolder + str(rank).zfill(3)+"_"

time.strftime("%Y-%m-%d %H:%M:%S")


#append a '/' if necessary
if(h5dir[-1] != '/'): h5dir += '/'
if(extrasDir[-1] != '/'): extrasDir += '/'

#The first line picks out the files that contain "volume_" in the directory, extrasDir
#The sorting should sort in numerical order
volumeXML, particlesTXT, gridPointsTXT, viewXML, timeTXT,\
bh13D, bh23D, bh33D, trace3D, trace23D, stateList = getLists(extrasDir)
print("stateList: {}".format(stateList))

def density(): return PlotDens
def bsq2r(): return PlotBsq2r and not density() #Can't have 2 volume plots
def bh_formed(): return len(bh13D) > 0
def binary_formed(): return len(bh23D) > 0
def merge_formed(): return len(bh33D) > 0
def trace1(): return len(trace3D) > 0
def trace2(): return len(trace23D) > 0
def particles(): return len(particlesTXT) > 0
def gridPoints(): return len(gridPointsTXT) > 0
def fields(): return particles() or gridPoints()
def velocity(): return PlotVel

#This adjusts the bh_*.3d files so that the black hole doesn't show up earlier than it's supposed to
#This will use bh3 data to overwrite the empty bh1 and bh2 files whenever bh1 and bh3 appear together in one folder. 
fill_bh(bh_formed(), '1', extrasDir, stateList)
fill_bh(binary_formed(), '2', extrasDir, stateList)
fill_bh(merge_formed(), '3', extrasDir, stateList)

#Checking bh files again ################
bh13D, bh23D, bh33D = recheckBH(extrasDir)

print("density: {}".format(density()))
print("bsq2r: {}".format(bsq2r()))
print("fields: {}".format(fields()))
print("particles: {}".format(particles()))
print("gridPoints: {}".format(gridPoints()))
print("trace1: {}".format(trace1()))
print("trace2: {}".format(trace2()))
print("velocity: {}".format(velocity()))
print("BH1: {}".format(bh_formed()))
print("BH2: {}".format(binary_formed()))
print("BH3: {}".format(merge_formed()))

###############################################################################
#load the databases
###############################################################################

Bxdir = h5dir + "Bx.file_* database"
Bydir = h5dir + "By.file_* database"
Bzdir = h5dir + "Bz.file_* database"
rho_bdir = h5dir + "rho_b.file_* database"
bh1dir = extrasDir + "bh1_*.3d database"
bh2dir = extrasDir + "bh2_*.3d database"
bh3dir = extrasDir + "bh3_*.3d database"
trace1dir = extrasDir + "trace1_*.3d database"
trace2dir = extrasDir + "trace2_*.3d database"
vxdir = h5dir + "vx.file_* database"
vydir = h5dir + "vy.file_* database"
vzdir = h5dir + "vz.file_* database"
smallb2dir = h5dir + "smallb2.file_* database"

if density():
	LoadandDefine(rho_bdir, "rho_b")
	DefineScalarExpression("logrho","log10(<MHD_EVOLVE--rho_b>/" + max_density + ")")

if bsq2r():
	LoadandDefine(rho_bdir, "rho_b")
	LoadandDefine(smallb2dir, "smallb2")
	DefineScalarExpression("logbsq2r","log10(<MHD_EVOLVE--smallb2>/(2*<rho_b>), -200)")

if fields():
	LoadandDefine(Bxdir, "Bx")
	LoadandDefine(Bydir, "By")
	LoadandDefine(Bzdir, "Bz")
	DefineVectorExpression("BVec","{Bx,By,Bz}")

if bh_formed():
	print("Loading bh1's...")
	OpenDatabase(bh1dir)

if binary_formed():
	print("Loading bh2's...")
	OpenDatabase(bh2dir)

if merge_formed():
	print("Loading bh3's...")
	OpenDatabase(bh3dir)

if trace1():
	print("Loading Particle Tracer...")
	OpenDatabase(trace1dir)

if trace2():
	print("Loading Particle Tracer 2...")
	OpenDatabase(trace2dir)

if velocity():
	LoadandDefine(vxdir, 'vx')
	LoadandDefine(vydir, 'vy')
	LoadandDefine(vzdir, 'vz')
	DefineVectorExpression("vVec_temp","{vx,vy,vz}")
	DefineVectorExpression("vVec","if(gt(magnitude(vVec_temp),0.1),vVec_temp,{0,0,0})")#Remove small arrows

print("\tDone")

# Put the additional database into dbs list when you add a new database. 
dbs = []
plot_idx = []
###
if density():
	dbs += [rho_bdir];				plot_idx += ["density"]
if bsq2r():
	dbs += [smallb2dir, rho_bdir];	plot_idx += ["bsq2r"]
###
if fields():
	dbs += [Bxdir, Bydir, Bzdir]
if particles():
	plot_idx += ["particles"]
if gridPoints():
	plot_idx += ["gridPoints"]
###
if bh_formed():
	dbs += [bh1dir];				plot_idx += ["bh1"]
if binary_formed():
	dbs += [bh2dir];				plot_idx += ["bh2"]
if merge_formed():
	dbs += [bh3dir];				plot_idx += ["bh3"]
###
if trace1():
	dbs += [trace1dir];				plot_idx += ["trace1"]
if trace2():
	dbs += [trace2dir];				plot_idx += ["trace2"]
###
if velocity():
	dbs += [vxdir, vydir, vzdir];	plot_idx += ["vel"]
###
print("Databases loaded: {}".format(dbs))
print("Plotting: {}".format(plot_idx))

CreateDatabaseCorrelation("Everything", dbs, 0)
time.strftime("%Y-%m-%d %H:%M:%S")
# Use plot_idx.index("plot name") to find its idx
def idx(name):
	return plot_idx.index(name)

DeleteAllPlots()

#add Density Volume Plot (0)################
if density():
	vol = PlotVol(rho_bdir, "logrho", idx("density"))
#add bsq2r Plot ##################
if bsq2r():
	bsq_atts = PlotVol(smallb2dir, "logbsq2r", idx("bsq2r"))
#add particles-seeded Streamline Plot#####
if particles():
	stream_particles = PlotB(Bxdir, idx("particles"))
#add gridPoints-seeded Streamline Plot####
if gridPoints():
	stream_gridPoints = PlotB(Bxdir, idx("gridPoints"))
#add bhplots##############################
if bh_formed():
	PlotBH(bh1dir, '1', idx("bh1"))

if binary_formed():
	PlotBH(bh2dir, '2', idx("bh2"))

if merge_formed():
	PlotBH(bh3dir, '3', idx("bh3"))

#add particle tracer plots################
if trace1():
	PlotTrace(trace1dir, '1', idx("trace1"))

if trace2():
	PlotTrace(trace2dir, '2', idx("trace2"))

#Add velocity arrows #####################
if velocity():
	vector_atts = PlotVelocity(vxdir, "vVec", idx("vel"))

myView = GetView3D()
#Annotations and View ########################
txt = setAnnotations()

#Save window settings
setSave(saveFolder)

###############################################################################
#start the movie
###############################################################################

print("Starting filming")
time.strftime("%Y-%m-%d %H:%M:%S")

state = stateList[index]

print("Loading state {}".format(index))
SetTimeSliderState(index)

tcur = timeTXT[state][5:-4]
print("t/M = %g" % int(float(tcur)))
txt.text = "t/M = %g" % int(float(tcur))

if density(): print(extrasDir + volumeXML[state])
time.strftime("%Y-%m-%d %H:%M:%S")

print("Loading Attributes")
LoadAttribute(extrasDir + viewXML[state], myView)

if density():		LoadAttribute(extrasDir + volumeXML[state], vol)
if bsq2r():			LoadAttribute(bsq2rXML, bsq_atts)
if velocity():		LoadAttribute(vectorXML, vector_atts)

if particles():
	LoadAttribute(streamXML, stream_particles)
	stream_particles.pointList = getSeeds(extrasDir + particlesTXT[state])
	if gridPoints():
		stream_particles.singleColor = (0, 255, 0, 255)

if gridPoints():
	LoadAttribute(streamXML, stream_gridPoints)
	stream_gridPoints.pointList = getSeeds(extrasDir + gridPointsTXT[state])

### adjust the cm focus ###
CoM = getCoM(extrasDir + timeTXT[state])
myView.focus = CoM
CoM_x, CoM_y, CoM_z = CoM

###########################Load view

c1 = View3DAttributes()
LoadAttribute(extrasDir + viewXML[state], c1)
c1.focus = CoM

######implement loaded plot settings
print("Setting settings")
if density():
	SetActivePlots(idx("density"))
	SetPlotOptions(vol)
	if cutPlot: box(CoM_y, 1)
if bsq2r():
	SetActivePlots(idx("bsq2r"))
	SetPlotOptions(bsq_atts)
	if cutPlot: box(CoM_y, 1)
if particles():
	SetActivePlots(idx("particles"))
	SetPlotOptions(stream_particles)
if gridPoints():
	SetActivePlots(idx("gridPoints"))
	SetPlotOptions(stream_gridPoints)
if velocity():
	SetActivePlots(idx("vel"))
	SetPlotOptions(vector_atts)
	cylinder(CoM_x,CoM_y,45, 1)
	if cutPlot: box(CoM_y, 1)

def cross(a,b):
	x=a[1]*b[2]-a[2]*b[1]
	y=a[2]*b[0]-a[0]*b[2]
	z=a[0]*b[1]-a[1]*b[0]
	return (x,y,z)

def newton(x,f,y):#	adjust initial theta to match new theta not theta0, newtons method on eqn
	#				x+f*sin(2x)-y=0
	for i in range (0,10):
		x=x-(x+f*sin(2*x)-y)/(1+2*f*cos(2*x))
	return x


def rotate(view, nsteps, frame_start, frame_end):
	print("Rotating")

	ctrig = view
	myViewNormal = ctrig.viewNormal
	myViewUp = ctrig.viewUp


	print("frame start: " + str(frame_start) + "\tframe_end: " + str(frame_end))
	for i in range(frame_start, frame_end,1):
		#TODO: Change factor as wanted
		factor = Factor#factor slows down rotation when looking into jet,
		#			higher value slows down more.  0<factor<0.5
		#			factor=0: spins at constant rate
		#			factor=0.5: comes to instantaeneous stop at top & bottom
		theta = 2*pi*i/(nsteps)#(n-1) makes last frame same as first

		xhat=myViewNormal[0]
		yhat=myViewNormal[1]
		zhat=myViewNormal[2]

		rhat=sqrt(xhat*xhat+yhat*yhat)
		theta0=atan2(zhat,rhat)
		theta0=newton(theta0,factor,theta0)

		theta_temp=theta0+theta
		theta_new=theta_temp+factor*sin(2*theta_temp)
		

		z_new=sin(theta_new)
		y_new=cos(theta_new)*(yhat/rhat)
		x_new=cos(theta_new)*(xhat/rhat)
		viewNormal = (x_new, y_new, z_new)
		print("Normal ", viewNormal)
		perp=cross((xhat,yhat,0),(0,0,zhat))
		print("perp ", perp)
		viewUp=cross(perp,viewNormal)
		print("up: ", viewUp)

		c = View3DAttributes()
		c = view
		c.viewNormal = viewNormal
		c.focus = CoM
		c.viewUp = viewUp

		DrawAndSave(c)

rotate(c1, tot_frames, frame_start, frame_end)


xmltxt='/'.join(saveFolder.split('/')[:-1])+'/xml.txt'
if(isfile(xmltxt)==0):
	xt=open(xmltxt,'w')
	xt.write('vol:\n')
	xt.write(str(vol))
	xt.write('\n\n\n\nview:\n')
	xt.write(str(myView))
	xt.close()

sys.exit()
