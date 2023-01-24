import numpy as np
import os, sys
import time
import subprocess
import shutil

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    print(tools)
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants

sumoBinary = "C:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "bin" + os.sep + "sumo-gui.exe"

dir_path = os.path.dirname(os.path.realpath(__file__))

class TrafficProblemManager:

    networks = []
    temp = []
    debug_mode = False
    network_lanes = []
    current_emissions = {}

    def __init__(self,debug):
        self.temp.append(['.Original/'])
        self.debug_mode = debug

    def getStateLanes(self):
        lanes = traci.lane.getIDList()
        for lane in lanes:
            if ":" not in str(lane):
                self.network_lanes.append(lane)

    def runState(self, state, runparameter):

        print("Running State : " + state + "osm.sumocfg")
        sumoCmd = [sumoBinary, "-c",  dir_path + state + "osm.sumocfg", "--start"]
        if self.debug_mode: print("Starting SUMO")
        traci.start(sumoCmd)
        traci.gui.setSchema("View #0", "emissions")
        if self.debug_mode: print("Sumo Started")

        # Run the network in SUMO
        j = 0  # j is the time step
        # Set the end point
        if runparameter != -1:
            last_j = runparameter
        else:
            last_j = 10
        # See which lanes are in the network so that we can calculate pollution levels
        self.network_lanes = []
        self.getStateLanes()
        self.current_emissions = {}
        while (j < last_j):
            # for each time step

            time.sleep(0.1)
            traci.simulationStep()

            # Show the emissions on the map

            if self.current_emissions == {}:
                for lane in self.network_lanes:
                    self.current_emissions[lane] = traci.lane.getCO2Emission(lane)
                    traci.lane.setParameter(lane, "Emis", self.current_emissions[lane])
            else:
                for lane in self.network_lanes:
                    self.current_emissions[lane] += traci.lane.getCO2Emission(lane)
                    traci.lane.setParameter(lane, "Emis", self.current_emissions[lane]/j)

            j += 1
        traci.close(wait=False)





    def runAction(self,action, state, new_state):
        action = str(action).split(" ")
        print("Running action " + action[0] + ", " + action[1] + " on state " + state)

        print("TEMPORARY OVERRIDE TO BLOCK STREET 23353423#2")
        action[1] = "23353423#2"
        # Check action type
        if action[0] == "remove":
            # We need to remove a road
            print("Removing road : " + action[1])
            network_file = state + "osm.net.xml"
            # First we need to flatten file to plain XML:
            if self.debug_mode: print("Flattening network files to plain XML")

            # If the flatfiles path doesn't exist, make it
            if not os.path.isdir(dir_path + state + "flatfiles"):
                os.makedirs(dir_path + state + "flatfiles")
                print("Created new directory in " + state + "flatfiles")

            # Use subprocess to run netconvert to flatten the files to plain xml
            subprocess.call(["netconvert", "--sumo-net-file=" + dir_path + network_file, "--plain-output-prefix="  + dir_path+ state + "flatfiles/network"], shell=True)
            print("Outputted to " + state + "flatfiles/")

            # We need to remove edge from network.edg file

            Newfile = []  # Temporarily store new file

            # Read the edge file and store it into Newfile
            with open(dir_path + state + "flatfiles/network.edg.xml", "r") as f:
                Newfile = f.readlines()

            # Check if the directory of the new file exists yet
            if not os.path.isdir(dir_path + new_state + "flatfiles"):
                os.makedirs(dir_path + new_state + "flatfiles")
                print("Created new directory in " + new_state + "flatfiles")


            # Now rewrite the file but remove the unwanted connections
            with open(dir_path + new_state + "flatfiles/network.edg.xml", "w") as f:
                print("Successfully opened output file : " + new_state + "flatfiles/network.edg.xml")
                Delete = False
                for number, line in enumerate(Newfile):
                    if Delete == True:
                        if "</edge>" in line:
                            Delete = False
                            print("Removing line : " + str(line))
                        else:
                            print("Removing line : " + str(line))
                    else:
                        if "<edge id=\"" + str(action[1]) in line:
                            Delete = True
                            print("Removing line : " + str(line))

                        elif "<edge id=\"-" + str(action[1]) in line:
                            print("Removing line : " + str(line))
                            Delete = True
                        elif "<connection" in line and str(action[1]) in line:
                            print("Removing line : " + str(line))
                        else:
                            f.write(str(line) + "\n")

            print("Successfully updated edg file")

            # Update the connections file

            Newfile = []  # Temporarily store new file

            # Read the edge file and store it into Newfile
            with open(dir_path + state + "flatfiles/network.con.xml", "r") as f:
                Newfile = f.readlines()

            # Check if the directory of the new file exists yet
            if not os.path.isdir(dir_path + new_state + "flatfiles"):
                os.makedirs(dir_path + new_state + "flatfiles")
                print("Created new directory in " + new_state + "flatfiles")
            else:
                if self.debug_mode: print("Directory " + new_state + "flatfiles/ already exists")

            # Now rewrite the file but remove the unwanted connections

            with open(dir_path + new_state + "flatfiles/network.con.xml", "w") as f:
                print("Successfully opened output file : " + new_state + "flatfiles/network.con.xml")
                Delete = False
                for number, line in enumerate(Newfile):

                    if str(action[1]) in line:
                        print("Removing line : " + str(line))
                    else:
                        f.write(str(line) + "\n")

            print("Successfully updated edg file")

            # Copy the node, tll and typ files to the new directory
            print("Copying remaining files")

            if self.debug_mode: print("Copying node file")
            shutil.copyfile(dir_path + state + "flatfiles/network.nod.xml", dir_path + new_state + "flatfiles/network.nod.xml")
            if self.debug_mode: print("Copying traffic light file")
            shutil.copyfile(dir_path + state + "flatfiles/network.tll.xml", dir_path + new_state + "flatfiles/network.tll.xml")
            if self.debug_mode: print("Copying node file")
            shutil.copyfile(dir_path + state + "flatfiles/network.typ.xml", dir_path + new_state + "flatfiles/network.typ.xml")

            print("Done with plain xml files")

            # Create a new network file

            print("Rebuilding network from plainXML")
            print("Creating .net.xml file at " + new_state + "osm.net.xml")
            subprocess.run(["netconvert", "--node-files=" + dir_path + new_state + "flatfiles/network.nod.xml","--edge-files=" + dir_path + new_state + "flatfiles/network.edg.xml", "--connection-files=" + dir_path + new_state + "flatfiles/network.con.xml", "--tllogic-files=" + dir_path + new_state + "flatfiles/network.tll.xml", "--type-files=" + dir_path + new_state + "flatfiles/network.typ.xml", "--output-file=" + dir_path + new_state + "osm.net.xml", "--lefthand"])
            print("done")

            # Create a trips file

            print("Creating trips file")
            subprocess.call(["randomTrips.py", "--net-file=" + dir_path + new_state + "osm.net.xml", "-e 350", "--output-trip-file=" + dir_path + new_state + "osm.trips.xml", "--period=0.1", "--validate"], shell=True)
            print("done")
            print("Creating Routes file")
            subprocess.call(["duarouter", "--net-file=" + dir_path + new_state + "osm.net.xml", "--route-files=" + dir_path + new_state + "osm.trips.xml", "--output-file=" + dir_path + new_state + "osm.rou.xml"], shell=True)
            print("done")

            # Create the config file

            print("Creating Configuration file")
            config_file = "<?xml version=\"1.0\" encoding=\"iso-8859-1\"?>\n"
            config_file = config_file + "\n"
            config_file = config_file + "<configuration xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.sf.net/xsd/sumoConfiguration.xsd\">\n"
            config_file = config_file + "\n"
            config_file = config_file + "<input>\n"
            config_file = config_file + "<net-file value=\"osm.net.xml\"/>\n"
            config_file = config_file + "<route-files value=\"osm.rou.xml\"/>\n"
            config_file = config_file + "</input>\n"
            config_file = config_file + "\n"
            config_file = config_file + "<processing>\n"
            config_file = config_file + "<ignore-route-errors value=\"true\"/>\n"
            config_file = config_file + "</processing>\n"
            config_file = config_file + "\n"
            config_file = config_file + "<routing>\n"
            config_file = config_file + "<device.rerouting.adaptation-steps value=\"18\"/>\n"
            config_file = config_file + "<device.rerouting.adaptation-interval value=\"10\"/>\n"
            config_file = config_file + "</routing>\n"
            config_file = config_file + "<time>\n"
            config_file = config_file + "<begin value=\"0\"/>\n"
            config_file = config_file + "<end value=\"1000\"/>\n"
            config_file = config_file + "</time>\n"
            config_file = config_file + "\n"
            config_file = config_file + "</configuration>"

            with open(dir_path + new_state + "osm.sumocfg",'w') as f:
                f.write(config_file)
            print("done")








