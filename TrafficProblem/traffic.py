import numpy as np
import os, sys
import time
import subprocess
import shutil
import pandas as pd
from multiprocessing import Pool

#
# if 'SUMO_HOME' in os.environ:
#     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
#     print(tools)
#     sys.path.append(tools)
# else:
#     sys.exit("please declare environment variable 'SUMO_HOME'")
#
# if 'SUMO_HOME' in os.environ:
#     tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
#     print(tools)
#     sys.path.append(tools)
# else:
#     sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
import traci.constants

sumoBinary = "D:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "bin" + os.sep + "sumo.exe"

dir_path = os.path.dirname(os.path.realpath(__file__))




class TrafficProblemManager:

    networks = []
    temp = []
    debug_mode = False
    network_lanes = []
    current_emissions = {}
    traffic_flows = []
    current_vehicles = []
    lane_information = {}
    initial_matrix = []

    def __init__(self,debug):
        self.temp.append(['.Original/'])
        self.debug_mode = debug


    def getStateLanes(self):
        lanes = traci.lane.getIDList()
        for lane in lanes:
            if ":" not in str(lane):
                self.network_lanes.append(lane)

    def getCurrentVehicles(self):
        self.current_vehicles = []  # Reset vehicles array

        vehicles = traci.vehicle.getIDList()  # Get the ID's of all vehicles in the network

        # get vehicle locations
        locations = []  # Temp vehicle locations array
        for vehicle in vehicles:
            locations.append(traci.vehicle.getLaneID(vehicle))

        # get vehicle speeds
        speeds = []
        for vehicle in vehicles:
            speeds.append(traci.vehicle.getSpeed(vehicle))

        self.current_vehicles = [vehicles, locations, speeds]
        return self.current_vehicles

    def getLaneInformation(self):
        lanes = traci.lane.getIDList()

        # Get the speed limits of each lane
        speedlimits = []
        for lane in lanes:
            speedlimits.append(traci.lane.getMaxSpeed(lane))

        self.lane_information = dict(zip(lanes, speedlimits))
        return self.lane_information


    def runState(self, state, runparameter):

        print("Running State : " + state + "osm.sumocfg")
        print(dir_path + state)
        sumoCmd = [sumoBinary, "-c",  dir_path + state + "osm.sumocfg", "--start", "--quit-on-end"]
        if self.debug_mode: print("Starting SUMO")
        traci.start(sumoCmd)
        #traci.gui.setSchema("View #0", "emissions")
        #traci.gui.setSchema("View #0", "faster standard")
        if self.debug_mode: print("Sumo Started")

        # Run the network in SUMO
        j = 0  # j is the time step
        # Set the end point
        if runparameter != -1:
            last_j = runparameter
        else:
            last_j = 500
        # See which lanes are in the network so that we can calculate pollution levels
        # self.network_lanes = []
        # self.getStateLanes()
        # self.current_emissions = {}
        traci.simulationStep(50)
        initial_journey_time = 0
        while (j < last_j):
            # for each time step
            traci.simulationStep()
            if j == 5:
                route = traci.simulation.findRoute("-23353430#1", "23353772#2")
                traci.route.add("TestRoute",route.edges)
                traci.vehicle.add("TestVehicle", "TestRoute")
                traci.vehicle.highlight("TestVehicle")
                initial_journey_time = traci.simulation.getTime()
            if j > 5:
                if self.check_vehicle_position("TestVehicle", "23353772#2"):
                    total_journey_time = traci.simulation.getTime() - initial_journey_time
                    j = last_j
                    traci.close(wait=False)
                    return(total_journey_time)

            j += 1
        traci.close(wait=False)

    def check_vehicle_position(self, VehID, TargetEdge):
        current_edge_ID = traci.vehicle.getRoadID(VehID)

        if (current_edge_ID == TargetEdge):
            return True
        else:
            return False

    def get_traffic_flow(self):

        # Calculate the rate of traffic flow. We do this by looking at the list of all vehicles in the network, checking
        # the roads speed limit, then comparing with the speed of the vehicle

        self.getCurrentVehicles()
        self.getLaneInformation()
        speed_limit = []
        for LaneID in self.current_vehicles[1]:
            speed_limit.append(float(self.lane_information[str(LaneID)]))

        flow_rates = []
        for i in range(0, np.shape(self.current_vehicles)[1]):
            # For each car, compare the speed with the road speed limit

            car_speed = float(self.current_vehicles[2][i])
            road_speed = float(speed_limit[i])
            flow_rates.append(car_speed / road_speed)


        #
        #     speedLimit = [speedLimit for SpeedLimit in self.lane_information if str(LaneID) in self.lane_information[0]]
        #     print(speedLimit)
        self.traffic_flows.append(np.mean(flow_rates))
        return np.mean(flow_rates)


    def runAction(self,action, state, new_state, flatfiles=True):
        action = str(action).split(" ")
        if self.debug_mode: print("Running action " + action[0] + ", " + action[1] + " on state " + state)
        #("Running action " + action[0] + ", " + action[1] + " on state " + state)
        # Check action type
        if action[0] == "remove":
            # We need to remove a road
            if self.debug_mode: print("Removing road : " + action[1])
            network_file = state + "osm.net.xml"

            # if flatfiles:
            #     # First we need to flatten file to plain XML:
            #     if self.debug_mode: print("Flattening network files to plain XML")
            #
            #     # If the flatfiles path doesn't exist, make it
            #     if not os.path.isdir(dir_path + state + "flatfiles"):
            #         os.makedirs(dir_path + state + "flatfiles")
            #         if self.debug_mode: print("Created new directory in " + state + "flatfiles")
            #
            #     # Use subprocess to run netconvert to flatten the files to plain xml
            #     subprocess.call(["netconvert", "--sumo-net-file=" + dir_path + network_file, "--plain-output-prefix="  + dir_path+ state + "flatfiles\\network"], shell=True)
            #     if self.debug_mode: print("Outputted to " + state + "flatfiles\\")

            # We need to remove edge from network.edg file

            Newfile = []  # Temporarily store new file

            # # Read the edge file and store it into Newfile
            # with open(dir_path + state + "flatfiles\\network.edg.xml", "r") as f:
            #     Newfile = f.readlines()
            #
            # # Check if the directory of the new file exists yet
            # if not os.path.isdir(dir_path + new_state + "flatfiles"):
            #     os.makedirs(dir_path + new_state + "flatfiles")
            #     if self.debug_mode: print("Created new directory in " + new_state + "flatfiles")
            #
            #
            # # Now rewrite the file but remove the unwanted connections
            # with open(dir_path + new_state + "flatfiles/network.edg.xml", "w") as f:
            #     if self.debug_mode: print("Successfully opened output file : " + new_state + "flatfiles/network.edg.xml")
            #     Delete = False
            #     for number, line in enumerate(Newfile):
            #         if Delete == True:
            #             if "</edge>" in line:
            #                 Delete = False
            #                 if self.debug_mode: print("Removing line : " + str(line))
            #             else:
            #                 if self.debug_mode: print("Removing line : " + str(line))
            #         else:
            #             if "<edge id=\"" + str(action[1]) in line:
            #                 Delete = True
            #                 if self.debug_mode: print("Removing line : " + str(line))
            #             elif "<edge id=\"" + str(action[1]).replace("-","") in line:
            #                 if self.debug_mode: print("Removing line : " + str(line))
            #                 Delete = True
            #             elif "<connection" in line and str(action[1]) in line:
            #                 if self.debug_mode: print("Removing line : " + str(line))
            #             else:
            #                 f.write(str(line) + "\n")
            #
            # if self.debug_mode: print("Successfully updated edg file")
            #
            # # Update the connections file
            #
            # Newfile = []  # Temporarily store new file
            #
            # # Read the edge file and store it into Newfile
            # with open(dir_path + state + "flatfiles/network.con.xml", "r") as f:
            #     Newfile = f.readlines()
            #
            # # Check if the directory of the new file exists yet
            # if not os.path.isdir(dir_path + new_state + "flatfiles"):
            #     os.makedirs(dir_path + new_state + "flatfiles")
            #     if self.debug_mode: print("Created new directory in " + new_state + "flatfiles")
            # else:
            #     if self.debug_mode: print("Directory " + new_state + "flatfiles/ already exists")
            #
            # # Now rewrite the file but remove the unwanted connections
            #
            # with open(dir_path + new_state + "flatfiles/network.con.xml", "w") as f:
            #     if self.debug_mode: print("Successfully opened output file : " + new_state + "flatfiles/network.con.xml")
            #     Delete = False
            #     for number, line in enumerate(Newfile):
            #
            #         if str(action[1]).replace("-","") in line:
            #             if self.debug_mode:
            #                 print("Removing line : " + str(line))
            #         else:
            #             f.write(str(line) + "\n")
            #
            # if self.debug_mode: print("Successfully updated edg file")
            #
            # Newfile = []  # Temporarily store new file
            #
            # # Read the edge file and store it into Newfile
            # with open(dir_path + state + "flatfiles/network.tll.xml", "r") as f:
            #     Newfile = f.readlines()
            #
            # # Check if the directory of the new file exists yet
            # if not os.path.isdir(dir_path + new_state + "flatfiles"):
            #     os.makedirs(dir_path + new_state + "flatfiles")
            #     print("Created new directory in " + new_state + "flatfiles")
            # else:
            #     if self.debug_mode: print("Directory " + new_state + "flatfiles/ already exists")
            #
            # # Now rewrite the file but remove the unwanted connections
            #
            # with open(dir_path + new_state + "flatfiles/network.tll.xml", "w") as f:
            #     if self.debug_mode: print("Successfully opened output file : " + new_state + "flatfiles/network.con.xml")
            #     Delete = False
            #     for number, line in enumerate(Newfile):
            #
            #         if str(action[1]) in line:
            #             if self.debug_mode:
            #                 print("Removing line : " + str(line))
            #         else:
            #             f.write(str(line) + "\n")
            #
            # if self.debug_mode: print("Successfully updated tll file")
            #
            # # Copy the node and typ files to the new directory
            # if self.debug_mode: print("Copying remaining files")
            #
            # if self.debug_mode: print("Copying node file")
            # shutil.copyfile(dir_path + state + "flatfiles/network.nod.xml", dir_path + new_state + "flatfiles/network.nod.xml")
            #
            # if self.debug_mode: print("Copying node file")
            # shutil.copyfile(dir_path + state + "flatfiles/network.typ.xml", dir_path + new_state + "flatfiles/network.typ.xml")
            #
            # if self.debug_mode: print("Done with plain xml files")
            #
            # # Create a new network file
            #
            # if self.debug_mode: print("Rebuilding network from plainXML")
            # if self.debug_mode: print("Creating .net.xml file at " + new_state + "osm.net.xml")
            # subprocess.run(["netconvert", "--node-files=" + dir_path + new_state + "flatfiles/network.nod.xml","--edge-files=" + dir_path + new_state + "flatfiles/network.edg.xml", "--connection-files=" + dir_path + new_state + "flatfiles/network.con.xml", "--tllogic-files=" + dir_path + new_state + "flatfiles/network.tll.xml", "--type-files=" + dir_path + new_state + "flatfiles/network.typ.xml", "--output-file=" + dir_path + new_state + "osm.net.xml", "--lefthand", "--no-warnings", "--no-turnarounds"])
            #
            # # Create a trips file
            #
            # print("Creating trips file")
            # # subprocess.call(["python.exe","D:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "tools" + os.sep + "randomTrips.py", "--net-file=" + dir_path + new_state + "osm.net.xml", "-e 350", "--output-trip-file=" + dir_path + new_state + "osm.trips.xml", "--route-file=" + dir_path + new_state + "osm.rou.xml", "--period=0.1", "--validate"], shell=True)
            # subprocess.call(["python.exe","D:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "tools" + os.sep + "randomTrips.py", "--net-file=" + dir_path + new_state + "osm.net.xml", "--output-trip-file=" + dir_path + new_state + "osm.trips.xml", "--route-file=" + dir_path + new_state + "osm.rou.xml", "--period=0.4", "--validate"], shell=True)
            #
            #
            # # Create the config file
            #
            # if self.debug_mode: print("Creating Configuration file")
            # config_file = "<?xml version=\"1.0\" encoding=\"iso-8859-1\"?>\n"
            # config_file = config_file + "\n"
            # config_file = config_file + "<configuration xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.sf.net/xsd/sumoConfiguration.xsd\">\n"
            # config_file = config_file + "\n"
            # config_file = config_file + "<input>\n"
            # config_file = config_file + "<net-file value=\"osm.net.xml\"/>\n"
            # config_file = config_file + "<route-files value=\"osm.rou.xml\"/>\n"
            # config_file = config_file + "</input>\n"
            # config_file = config_file + "\n"
            # config_file = config_file + "<processing>\n"
            # config_file = config_file + "<ignore-route-errors value=\"true\"/>\n"
            # config_file = config_file + "</processing>\n"
            # config_file = config_file + "\n"
            # config_file = config_file + "<routing>\n"
            # config_file = config_file + "<device.rerouting.adaptation-steps value=\"18\"/>\n"
            # config_file = config_file + "<device.rerouting.adaptation-interval value=\"10\"/>\n"
            # config_file = config_file + "</routing>\n"
            # config_file = config_file + "<time>\n"
            # config_file = config_file + "<begin value=\"0\"/>\n"
            # config_file = config_file + "<end value=\"1000\"/>\n"
            # config_file = config_file + "</time>\n"
            # config_file = config_file + "\n"
            # config_file = config_file + "</configuration>"
            #
            # with open(dir_path + new_state + "osm.sumocfg",'w') as f:
            #     f.write(config_file)
            # if self.debug_mode: print("done")
            subprocess.run(["netconvert", "--sumo-net-file=" + dir_path + new_state + "osm.net.xml", "--lefthand", "--no-warnings", "--no-turnarounds"])
            subprocess.call(["python.exe","D:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "tools" + os.sep + "randomTrips.py", "--net-file=" + dir_path + new_state + "osm.net.xml", "--route-file=" + dir_path + new_state + "osm.rou.xml", "--period=0.4"], shell=True)


    def convert_network_to_matrix(self, state):

        # Get nodes
        if self.debug_mode:
            print("Flattening network files to plain XML")

        # If the flatfiles path doesn't exist, make it
        if not os.path.isdir(dir_path + state + "flatfiles"):
            os.makedirs(dir_path + state + "flatfiles")
            print("Created new directory in " + state + "flatfiles")
        network_file = state + "osm.net.xml"
        # Use subprocess to run netconvert to flatten the files to plain xml
        #subprocess.call(["netconvert", "--sumo-net-file=" + dir_path + network_file, "--plain-output-prefix=" + dir_path + state + "flatfiles\\network"], shell=True)
        print("Outputted to " + state + "flatfiles\\")


        # Read the nodes file and convert to csv
        NodesFile = []
        with open(dir_path + state + "flatfiles\\network" + ".nod.xml", "r") as f:
            for line in f.readlines():
                if "<node id=" in line:
                    temp = line.split("\"")
                    NodesFile.append([temp[1],temp[3],temp[5]])

        pd.set_option('display.max_columns', None)
        column_names = ["Node ID", "x", "y"]
        Nodes = pd.DataFrame(NodesFile, columns=column_names)

        #Nodes.to_csv(dir_path + state + "flatfiles\\nodes.csv", index=False)

        print("Making edges_file")
        # Convert edge file to CSV
        column_names = ["Edge ID", "From", "To"]
        edges_file = pd.DataFrame(columns=column_names)
        # edges_file = pd.concat([edges_file, pd.DataFrame([[0,0,0]], columns=column_names)])
        # print(edges_file)
        with open(dir_path + state + "flatfiles\\network" + ".edg.xml", "r") as f:
            for line in f.readlines():
                if "<edge id=" in line:
                    temp = line.split("\"")
                    # Check if the edge is already in the edges csv (but going the opposite direction)
                    if temp[3] in edges_file['To'].values:
                        output = edges_file[(edges_file['From'] == temp[5]) & (edges_file['To'] == temp[3])]

                        if output.empty:
                            #print(output)
                            new_row = [temp[1], temp[3], temp[5]]
                            if ("23353430#1" not in temp[1]) & ("23353772#2" not in temp[1]): # this is used to remove the test streets!
                                edges_file = pd.concat([edges_file, pd.DataFrame([new_row], columns=column_names)])
                    else:
                        new_row = [temp[1], temp[3], temp[5]]
                        if ("23353430#1" not in temp[1]) & ("23353772#2" not in temp[1]):
                            edges_file = pd.concat([edges_file, pd.DataFrame([new_row], columns=column_names)])




        pd.set_option('display.max_columns', None)

        # Edges = pd.DataFrame(EdgesFile, columns=column_names)

        edges_file.to_csv(dir_path + state + "flatfiles\\edges.csv", index=False)
        #
        # # Create a matrix to store the network
        # Network_Matrix = np.zeros(shape=(Nodes.shape[0],Nodes.shape[0]-1))
        # # Populate the network matrix
        # connection_counter = 0
        # for index,row in Edges.iterrows():
        #     # For each edge in the edges csv
        #     #Add connection between index(from) to index(to) (we need the index since nodes arent listed in order)
        #     From_index = list(np.where(Nodes["Node ID"] == row[1])[0])[0] - 1
        #     To_index = list(np.where(Nodes["Node ID"] == row[2])[0])[0] - 1
        #
        #     Network_Matrix[From_index,To_index] = int(index)
        #     connection_counter += 1
        #
        # Network_Matrix[Nodes.shape[0] - 1, 0] = int(connection_counter)
        # Network_Matrix[Nodes.shape[0]-1,1:] = 0
        #
        # DF2 = pd.DataFrame(Network_Matrix)
        # DF2.to_csv(dir_path + state + "flatfiles\\network.csv")
        print("Done Converting Matrix to CSV")
    state = ""

    def run_network_reduction_step(self, state):
        # This function will run through the network and manually delete or add one edge at a time.
        self.initial_matrix = pd.read_csv(dir_path + state + "flatfiles\\edges.csv")
        return self.initial_matrix

    def run_network_reduction_function(self, edge):


        state = "\\Networks\\Original\\"

        #TrafficProblemManager.runAction("remove " + edge, state, "\\Networks\\Temp\\" + edge + "\\", flatfiles=False)
        self.runAction("remove " + edge, state, "\\Networks\\Temp\\" + edge + "\\", flatfiles=False)
        #
        # print("Running network : " + str(counter_pool) + " of " + str(2597))
        output = self.runState("\\Networks\\Temp\\" + edge + "\\", 10000)
        # counter_pool = counter_pool + 1
        # #return output
        return [edge, output]


