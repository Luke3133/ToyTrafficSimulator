# BO with grakel
import grakel as gk
import os
import subprocess
import pandas as pd
import numpy as np
import sumolib
dir = os.path.dirname(os.path.realpath(__file__))


class GraphBO:
    all_graphs = []
    current_graphs = []

    def __init__(self, action_set):
        print("Starting GraphBO Package")

        # Calculate the graphs of each traffic network and store them in a list of grakel.graph objects
        graphs = list()
        for action in action_set:
            # For each action in the full set of all available combinations of actions (powerset)
            # Calculate the matrix of each action
            this_action = action_set.index(action)
            output = convert_network_to_matrix(str(this_action) + "\\")
            graphs.append(gk.Graph(output))
        print(graphs)

        # Check if the kernel_matrix exists, if not, make it using gk.Randomwalk. If it does, load from file
        if not os.path.isfile(dir + os.sep + "kernel_matrix.csv"):
            self.kernelfunc = gk.RandomWalk(normalize=True)
            self.kernel = self.kernelfunc.fit_transform(graphs)
            dataframe = pd.DataFrame(self.kernel)
            dataframe.to_csv(dir + os.sep + "kernel_matrix.csv", index=False)

            self.kernel = self.kernel.round(decimals=5).to_numpy()
        else:
            self.kernel = pd.read_csv(dir + os.sep + "kernel_matrix.csv")
            self.kernel = self.kernel.round(decimals=5)
            self.kernel = self.kernel.to_numpy()

    def GP_Train(self, train_x_index, train_y):
        self.x = train_x_index
        self.y = train_y
    def GP_New_X(self, new_x_index, train_x_index, train_x, train_y):
        # print(train_x)
        # print(train_x_index)
        # print(new_x_index)
        # Proceed with noise free gaussian process
        # print(self.kernel)

        k_x_star_x = []
        for j in train_x_index:
            for k in new_x_index:
                k_x_star_x.append(self.kernel[j, k])
        k_x_star_x = np.array(k_x_star_x).reshape(len(new_x_index), len(train_x_index))
        print(k_x_star_x)
        k_x_star_x_star = []
        for j in new_x_index:
            for k in new_x_index:
                k_x_star_x_star.append(self.kernel[j, k])
        k_x_star_x_star = np.array(k_x_star_x_star).reshape(len(new_x_index), len(new_x_index))
        print(k_x_star_x_star)

        k_x_x = []
        for j in train_x_index:
            for k in train_x_index:
                k_x_x.append(self.kernel[j, k])
        k_x_x = np.array(k_x_x).reshape(len(train_x_index), len(train_x_index))
        # print(k_x_x)
        k_x_x_inverse = np.linalg.inv(k_x_x)
        # print(k_x_x_inverse)
        k_x_star_x_k_x_x_inverse = k_x_star_x.dot(k_x_x_inverse)
        # print(k_x_star_x_k_x_x_inverse)
        mean = k_x_star_x_k_x_x_inverse.dot(train_y)
        # print(k_x_star_x_k_x_x_inverse_y)

        sd_temp = k_x_star_x.dot(k_x_x_inverse)
        sd_temp = sd_temp.dot(np.transpose(k_x_star_x))
        sd = np.subtract(k_x_star_x_star, sd_temp)
        return mean, sd









    def GP(self, old_data, new_data = ""):
        # Calculate the posterior mean and covariance matrix
        print("GP")
        kernel = self.kernel_func(old_data, new_data, "Random-Walk")

        return 5


    def kernel_func(self, old_data, new_data , type):

        match type:
            case "Random-Walk":
                # Calculate the kernel matrix for our data
                print("Random-Walk kernel")


def convert_network_to_matrix(state):
    dir_path = dir + "\\TrafficProblem\\Networks\\Temp\\"
    # If the matrix already exists, we don't need to make it again
    if os.path.isfile(dir_path + state + "network.csv"):
        network_matrix = pd.read_csv(dir_path + state + "network.csv")
        return network_matrix.to_numpy()

    # If the nodes path doesn't exist, make it and populate it else, open it
    nodes = []
    if not os.path.isfile(dir_path + "Nodes\\nodes.csv"):

        if not os.path.isdir(dir_path + "Nodes"):
            os.makedirs(dir_path + "Nodes")

        # Make the flat files for just one network (I never delete nodes, so no issues using the same nodes file)
        if not os.path.isdir(dir_path + state + "flatfiles"):
            os.makedirs(dir_path + state + "flatfiles")
            network_file = state + "osm.net.xml"
            # Use subprocess to run netconvert to flatten the files to plain xml
            subprocess.call(["netconvert", "--sumo-net-file=" + dir_path + network_file, "--plain-output-prefix=" + dir_path + state + "flatfiles\\network"], shell=True)

        NodesFile = []
        with open(dir_path + state + "flatfiles\\network" + ".nod.xml", "r") as f:
            for line in f.readlines():
                if "<node id=" in line:
                    temp = line.split("\"")
                    NodesFile.append([temp[1], temp[3], temp[5]])

        pd.set_option('display.max_columns', None)
        column_names = ["Node ID", "x", "y"]
        nodes = pd.DataFrame(NodesFile, columns=column_names)

        nodes.to_csv(dir_path + "Nodes\\nodes.csv", index=False)
    else:
        nodes = pd.read_csv(dir_path + "Nodes\\nodes.csv")

    # Open network file with sumolib
    net = sumolib.net.readNet(dir_path + state + "osm.net.xml")

    # Matrix to store the graph
    network_matrix = np.zeros(shape=(nodes.shape[0] - 1, nodes.shape[0] - 1))

    # For every edge in the network, add edge to matrix
    for edge in net.getEdges():
        from_index = list(np.where(nodes["Node ID"] == edge.getFromNode().getID())[0])[0] - 1
        to_index = list(np.where(nodes["Node ID"] == edge.getToNode().getID())[0])[0] - 1
        network_matrix[from_index, to_index] = 1

    DF2 = pd.DataFrame(network_matrix)
    DF2.to_csv(dir_path + state + "network.csv", index=False)
    print("Done Converting Matrix to CSV for state: " + str(state))

    return network_matrix
