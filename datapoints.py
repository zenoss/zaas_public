import Globals
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from transaction import commit

dmd = ZenScriptBase(connect=True).dmd

counts = {}

for coll in dmd.Monitors.Performance.objectValues("PerformanceConf"):
    counts[coll.id] = {}

    for d in coll.devices():

		#device.collectDevice() (for modeling)

        d = d.primaryAq()

        dc = d.deviceClass().primaryAq().getPrimaryId()[10:]

        if not counts[coll.id].has_key(dc):

          counts[coll.id][dc] = {'devices': 0, 'datapoints': 0}

        comps = d.getMonitoredComponents()

        datapoints = sum([comp.getRRDDataPoints() for comp in comps], []) + d.getRRDDataPoints()

        counts[coll.id][dc]['devices'] += 1

        counts[coll.id][dc]['datapoints'] += len(datapoints)

###############################

data = counts
 
TotalDeviceCount=0
TotalDataPointCount=0

for Collector in data:
    DeviceCount=0
    DataPointCount=0
    
    for DeviceClass in data[Collector]:
        DataPointCount += data[Collector][DeviceClass]['datapoints']
        DeviceCount += data[Collector][DeviceClass]['devices']
        TotalDataPointCount += data[Collector][DeviceClass]['datapoints']
        TotalDeviceCount += data[Collector][DeviceClass]['devices']     
    
    print "\n" + Collector + " Device Count: " + str(DeviceCount)
    print Collector + " Data Point Count: " + str(DataPointCount)
    if DeviceCount == 0:
        print Collector + " Average Data Points per Device: 0"
    else:
        print Collector + " Average Data Points per Device: " + str(DataPointCount / DeviceCount)

print "\n---------------------------"
print "Total Device Count: " + str(TotalDeviceCount)
print "Total Data Point Count: " + str(TotalDataPointCount)
print "Total Average Data Points per Device: " + str(TotalDataPointCount / TotalDeviceCount) +"\n"
