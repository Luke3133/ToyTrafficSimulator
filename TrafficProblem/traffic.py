import numpy as np
import os, sys
import time
import subprocess
import shutil
import pandas as pd
from multiprocessing import Pool
from itertools import chain, combinations
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
    mystreet = "-23353430"
    endstreet = "-23353724#9"
    crude_counter=0

    test_cars = []
    test_street = "-23353548#1" # We wish to reduce traffic on this street
    # action_set = ["-25156946#0","-23353543","-23353378#0","-23353548#2","-23353532#3"]
    action_set = ["-1069087493#1","-23353548#1","-25156946#0","-23353553#0","-23353532#3","-1082152568"]
    test_set = []
    def __init__(self,debug):
        self.temp.append(['.Original/'])
        self.debug_mode = debug

    def set_test_set(self,state, start, end):
        # Generate start points
        cov = np.matrix([[4000,0],[0,4000]])
        z = np.random.multivariate_normal(start,cov, size=5)
        z2 = np.random.multivariate_normal(end, cov, size=5)

        Nodes = pd.read_csv(dir_path + state + "flatfiles\\nodes.csv")
        Edges = pd.read_csv(dir_path + state + "flatfiles\\edges.csv")
        Node_ID = Edges['Edge ID'].tolist()
        From = Edges['From'].tolist()
        To = Edges['To'].tolist()
        Node_Locations = np.array([Nodes['x'],Nodes['y']]).T

        closest_start_edges = []
        closest_end_edges = []
        #Pick spawn edge
        for car in z:
            distances = []
            # Find the nearest node
            for node in Node_Locations:
                distances.append(np.linalg.norm(car - node))
            index = distances.index(sorted(distances)[0])
            node_id = Nodes['Node ID'][index]
            found = False
            try:
                edge_index = From.index(node_id)
                closest_start_edges.append(str(Node_ID[edge_index]))
                found = True
            except ValueError:
                print("Value " + str(node_id) + " not found in From")
            if found == False:
                try:
                    edge_index = To.index(node_id)
                    closest_start_edges.append(str(Node_ID[edge_index]))
                except ValueError:
                    print("Value " + str(node_id) + " not found in To")
            #print("The car was generated on edge: " + closest_start_edges[-1])

        for car in z2:
            distances = []
            # Find the nearest end node
            for node in Node_Locations:
                distances.append(np.linalg.norm(car - node))
            index = distances.index(sorted(distances)[0])
            node_id = Nodes['Node ID'][index]
            found = False
            try:
                edge_index = From.index(node_id)
                closest_end_edges.append(str(Node_ID[edge_index]))
                found = True
            except ValueError:
                print("Value " + str(node_id) + " not found in From")

            if found == False:
                try:
                    edge_index = To.index(node_id)
                    closest_end_edges.append(str(Node_ID[edge_index]))
                    # print("Value " + str(node_id) + " found in To at " + str(edge_index))
                except ValueError:
                    print("Value " + str(node_id) + " not found in To")
            #print("The car will end on edge: " + closest_end_edges[-1])
        self.test_cars = np.array([closest_start_edges, closest_end_edges]).T
        return self.test_cars

    def generate_test_cases(self, action_set):
        test_set = powerset(action_set)
        self.test_set = list(test_set)
        return self.test_set


    def runState(self, state, runparameter, testvehicles = "", teststreet = ""):
        sumoCmd = [sumoBinary, "-c",  dir_path + state + "osm.sumocfg", "--time-to-teleport=10000", "--start", "--quit-on-end", "--verbose=False","--duration-log.disable=True","--duration-log.statistics=False", "--no-step-log=True","--threads=4"]
        if self.debug_mode: print("Starting SUMO")
        traci.start(sumoCmd)
        # Run the network in SUMO
        j = 0  # j is the time step
        # Set the end point
        if runparameter != -1:
            last_j = runparameter
        else:
            last_j = 500
        traci.simulationStep(50)
        initial_journey_time = {}
        total_journey_time = 0
        vehicles_still_travelling = []
        counter = 0
        for vehicle in testvehicles:
            vehicles_still_travelling.append(["TestVehicle_" + str(counter), vehicle[0], vehicle[1]])
            counter += 1

        while (j < last_j):
            # for each time step
            traci.simulationStep()
            if j == 5:
                # add test vehicles
                vehicle_counter = 0
                for vehicle in testvehicles:
                    # print(vehicle)
                    # print(vehicle[0])
                    # print(vehicle[1])
                    vehicle_route = traci.simulation.findRoute(fromEdge = str(vehicle[0]), toEdge= str(vehicle[1]))
                    traci.route.add("TestRoute_" + str(vehicle_counter),vehicle_route.edges)
                    traci.vehicle.add("TestVehicle_" + str(vehicle_counter), "TestRoute_" + str(vehicle_counter))
                    initial_journey_time["TestVehicle_" + str(vehicle_counter)] = traci.simulation.getTime()
                    vehicle_counter += 1
            if j > 6:
                for vehicle in vehicles_still_travelling:
                    if self.check_vehicle_position(vehicle[0], vehicle[2]):
                        # This vehicle has reached the end point
                        total_journey_time = total_journey_time + traci.simulation.getTime() - initial_journey_time[vehicle[0]]
                        #print(str(vehicle[0]) + " has reached the end!")
                        # Remove this vehicle from list
                        vehicles_still_travelling.remove(vehicle)
                       # print(vehicles_still_travelling)
                        #print(total_journey_time)
                    last_j = j + 500 # Play about with this value (It is used to set a cap on simulation times)

                if len(vehicles_still_travelling) == 0:
                    traci.close(wait=False)
                   #print(total_journey_time)
                    return total_journey_time

            if j > last_j:
                j = last_j
            j += 1
        for vehicle in vehicles_still_travelling:
            total_journey_time = total_journey_time + traci.simulation.getTime() - initial_journey_time[vehicle[0]]


        traci.close(wait=False)
        return total_journey_time

    def check_vehicle_position(self, VehID, TargetEdge):
        current_edge_ID = traci.vehicle.getRoadID(VehID)

        if (current_edge_ID == TargetEdge):
            return True
        else:
            return False
    def runAction(self,action, state, new_state, flatfiles=True):
        if self.debug_mode: print("Removing road(s) : " + str(action))
        network_file = state + "osm.net.xml"


        # Check if the directory of the new file exists yet
        if not os.path.isdir(dir_path + new_state):
            os.makedirs(dir_path + new_state)
            if self.debug_mode: print("Created new directory in " + new_state)

            # If the state already exists, no need to make it again. Skip to next step!!!
            final_actions = ""
            # prepare action set
            for this_action in action:
                if final_actions == "":
                    final_actions = str(this_action) + "," + str(this_action).replace("-", "")
                else:
                    final_actions = final_actions + "," + str(this_action) + "," + str(this_action).replace("-","")

            # subprocess.run(["netconvert", "--sumo-net-file=" + dir_path + state + "osm.net.xml", "--remove-edges.explicit", "" + action[1] + "," + action[1].replace("-","") + "","--output-file=" + dir_path + new_state + "osm.net.xml", "--lefthand", "--no-warnings", "--no-turnarounds"])#,  stdout=subprocess.DEVNULL)
            subprocess.run(["netconvert", "--sumo-net-file=" + dir_path + state + "osm.net.xml", "--remove-edges.explicit", "" + final_actions + "","--output-file=" + dir_path + new_state + "osm.net.xml", "--lefthand", "--no-warnings", "--no-turnarounds"],  stdout=subprocess.DEVNULL)
            subprocess.call(["python.exe", "D:\Program Files (x86)\Eclipse" + os.sep + "Sumo" + os.sep + "tools" + os.sep + "randomTrips.py",
                             "--net-file=" + dir_path + new_state + "osm.net.xml", "--route-file=" + dir_path + new_state + "osm.rou.xml", "--period=1", "--output-trip-file=" + dir_path + new_state + "osm.trips.xml"],  stdout=subprocess.DEVNULL)

            # # Create the config file

            if self.debug_mode: print("Creating Configuration file")
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
            if self.debug_mode: print("done")


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
            subprocess.call(["netconvert", "--sumo-net-file=" + dir_path + network_file, "--plain-output-prefix=" + dir_path + state + "flatfiles\\network"], shell=True)
            print("Outputted to " + state + "flatfiles\\")

        #
        # # Read the nodes file and convert to csv
        # NodesFile = []
        # with open(dir_path + state + "flatfiles\\network" + ".nod.xml", "r") as f:
        #     for line in f.readlines():
        #         if "<node id=" in line:
        #             temp = line.split("\"")
        #             NodesFile.append([temp[1],temp[3],temp[5]])
        #
        # pd.set_option('display.max_columns', None)
        # column_names = ["Node ID", "x", "y"]
        # Nodes = pd.DataFrame(NodesFile, columns=column_names)
        #
        # Nodes.to_csv(dir_path + state + "flatfiles\\nodes.csv", index=False)

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
                            # Finally, we check if the street is at the end of a node:
                            # If the parameter intlanes only has one value, it's an end node i.e. how many lane arrows does the junction have
                            node1_intlanes = 0
                            node2_intlanes = 0
                            with open(dir_path + state + "osm.net.xml", "r") as f2:
                                for lines2 in f2.readlines():
                                    if "<junction id=\"" + str(temp[3]) + "\"" in lines2:
                                        #Check the intlanes
                                        node1_intlanes = lines2.split("\"")[11].count(":")
                                    elif "<junction id=\"" + str(temp[5]) + "\"" in lines2:
                                        node2_intlanes = lines2.split("\"")[11].count(":")


                                if (node1_intlanes == 1 and node2_intlanes != 1) or (node1_intlanes != 1 and node2_intlanes == 1) or (node1_intlanes != 1 and node2_intlanes != 1):
                                    edges_file = pd.concat([edges_file, pd.DataFrame([new_row], columns=column_names)])

                    else:
                        new_row = [temp[1], temp[3], temp[5]]

                        node1_intlanes = 0
                        node2_intlanes = 0
                        with open(dir_path + state + "osm.net.xml", "r") as f2:
                            for lines2 in f2.readlines():
                                if "<junction id=\"" + str(temp[3]) + "\"" in lines2:
                                    node1_intlanes = lines2.split("\"")[11].count(":")
                                    #
                                    # if (temp[3] == "252887583"):
                                    #     print(node1_intlanes )
                                elif "<junction id=\"" + str(temp[5]) + "\"" in lines2:
                                    node2_intlanes = lines2.split("\"")[11].count(":")



                            if (node1_intlanes == 1 and node2_intlanes != 1) or (node1_intlanes != 1 and node2_intlanes == 1) or (node1_intlanes != 1 and node2_intlanes != 1):
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
        regen_network = True
        # Calculate this test_case
        test_streets = self.test_set[edge]

        if regen_network:
            if not os.path.isdir(dir_path + "\\Networks\\Temp\\" + edge + "\\"):
                self.runAction(test_streets, state, "\\Networks\\Temp\\" + edge + "\\")
        result = self.runState("\\Networks\\Temp\\" + str(edge) + "\\", 2000, self.test_cars)

        return result


def powerset(s):
    s = list(s)
    return chain.from_iterable(combinations(s,r) for r in range(len(s)+1))
