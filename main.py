import math

import numpy as np
import os, sys
import time
from multiprocessing import Pool
import tqdm
import pandas as pd
import shutil
from TrafficProblem.traffic import TrafficProblemManager
from itertools import chain
from pathlib import Path
dir_path = os.path.dirname(os.path.realpath(__file__))
from agent import Agent
from BO import GraphBO
import random
class DesignerController:
    # This class is used to represent the current method of iterating on sequential designs. The user can run the
    # state, look at the output and choose an action. This process continues until the user is satisfied.

    # Commands:
    # end - ends the design scenario TODO: Save the design episode to be viewed later
    # history - shows the state, action, reward history of the design episode
    # run {timestep} - by replacing {timestep}, you can choose how long to run the simulation for (defaults to 10)
    # action {action type} {action parameter},  you can perform an action on the state e.g "action remove {roadID}"

    # I programmed this controller so that it can be easily adapted to other design problems. Most of the heavy lifting
    # is done in the traffic.py script and the TrafficProblemManager class it contains.

    states = []
    actions = []
    rewards = []
    recommended_actions = []
    problemfiles = ""

    def __init__(self, problem_files, state_files, debug_mode, beta_1, beta_2, p_omega):
        self.problemfiles = problem_files
        self.statefiles = state_files

        if self.problemfiles == "TrafficProblem":
            self.TrafficManager = TrafficProblemManager(debug_mode)
            self.states.append("\\Networks\\Original\\")
            self.beta_1 = beta_1
            self.beta_2 = beta_2
            self.p_omega = p_omega
        self.actionManager()

    def actionManager(self):
        finished = False
        while not finished:
            # Await an action by the user
            next_action = input("Select next action")

            if str(next_action) == "end":
                finished = True
            elif str(next_action) == "history":
                print("The states history is : " + str(self.states))
                print("The action history is : " + str(self.actions))
                print("The reward history is : " + str(self.rewards))
            elif "run" in str(next_action):
                runparameter = str(next_action).replace("run","")  # runparameter can be blank depending on scenario!
                print(runparameter)
                if " " in runparameter:
                    runparameter = int(runparameter)
                else:
                    runparameter = -1
                self.rewards.append(self.TrafficManager.runState(self.states[-1], runparameter))
            elif "action" in str(next_action):
                # Run an action / update the state (action type value)
                self.actions.append(str(next_action).replace("action ",""))

                # Set the new state for the action to take us to
                if self.states[-1] == "\\Networks\\Original\\":
                    self.states.append("\\Networks\\1\\")
                else:
                    last_state = int(str(self.states[-1]).replace("\\Networks\\","").replace("\\",""))
                    self.states.append("\\Networks\\" + str(last_state + 1) + "\\")
                action = [str(next_action).replace("action remove ","")]
                self.TrafficManager.runAction(action, self.states[-2], self.states[-1])


                # self.new_turn(int(next_action), self.sta te[-1])
                # elif "crude" in str(next_action):
                # Generate the test vehicles
                # test_vehicles = self.TrafficManager.set_test_set(self.states[-1], [1729.64, 1183.30], [1549, 753])
                # test_vehicles = self.TrafficManager.set_test_set(self.states[-1], [1729.64, 1250], [1549, 725])
                test_vehicles = self.TrafficManager.set_test_set(self.states[-1], [2562, 412], [1752, 1392])
                # Generate teh action set
                test_streets = self.TrafficManager.generate_test_cases(self.TrafficManager.action_set)
                crude_output = []
                test_case_counter = 0
                self.TrafficManager.debug_mode = False
                for test_cases in test_streets:
                    # For every test scenario

                    # Make a directory to hold the networks
                    if not os.path.isdir(dir_path + "\\Networks\\Temp\\"):
                        os.makedirs(dir_path + "\\Networks\\Temp\\")

                    print((test_case_counter/len(test_streets))*100)
                    if not test_cases:
                        # # this is the case where we have the original network (no changes)
                        action = ["-120291722#2"]
                        self.TrafficManager.runAction(action,"\\Networks\\Original\\","\\Networks\\Temp\\" + str(test_case_counter) + "\\")
                        result = self.TrafficManager.runState("\\Networks\\Temp\\" + str(test_case_counter) + "\\", 2000, test_vehicles, self.TrafficManager.test_street)
                        crude_output.append(result)

                    else:
                        # this is the case where we make some changes
                        self.TrafficManager.runAction(test_cases, "\\Networks\\Original\\", "\\Networks\\Temp\\" + str(test_case_counter) + "\\")
                        result = self.TrafficManager.runState("\\Networks\\Temp\\" + str(test_case_counter) + "\\", 2000, test_vehicles, self.TrafficManager.test_street)
                        crude_output.append(result)
                    test_case_counter +=1

                min_output = min(crude_output)
                min_index = crude_output.index(min_output)
                df_row = [min_index, min_output]
                output_csv = pd.DataFrame([df_row], columns=["Design","Time"])
                output_csv.to_csv("History\\crudeoutput_final.csv", index=False)
                print(output_csv)
            elif "cars" in str(next_action):
                self.TrafficManager.set_test_set(self.states[-1], [1752, 1392], [2562, 412])
                print("\nThe test vehicles are:")
                print(self.TrafficManager.test_cars)
            elif "streets" in str(next_action):

                print("\nThe test streets are:")
                print(self.TrafficManager.test_set)
            elif "next" in str(next_action):
                if type(self.TrafficManager.test_cars) == list:
                    self.TrafficManager.set_test_set(self.states[-1], [1752, 1392], [2562, 412])
                self.TrafficManager.generate_test_cases(self.TrafficManager.action_set)
                test_streets = self.TrafficManager.test_set
                test_streets_vector = list(range(0,len(test_streets)))
                self.TrafficManager.debug_mode = False

                pool = Pool()
                result_list_tqdm = []
                for result in tqdm.tqdm(pool.imap(self.TrafficManager.run_network_reduction_function, test_streets_vector), total=len(test_streets)):
                    result_list_tqdm.append(result)

                min_result = min(result_list_tqdm)
                new_list = sorted(result_list_tqdm)
                print("\nOriginal list:")
                print(result_list_tqdm)
                print("\nNew List:")
                print(new_list)
                min_index = result_list_tqdm.index(min_result)
                print("The minimum value is: " + str(min_result) + ", located at: " + str(min_index))
                print("\nThe optimal streets are:")
                print(test_streets[min_index])
                data = {
                    "Design": [min_index],
                    "Time": [min_result]
                }
                df_row = pd.DataFrame(data)
                my_file = Path(dir_path + "\\History\\crudeoutput_final.csv")
                if my_file.is_file():
                    history = pd.read_csv("History\\crudeoutput_final.csv")
                    history = pd.concat([history, df_row])
                    history.to_csv("History\\crudeoutput_final.csv",index=False)
                else:

                    df_row = [min_index, min_result]
                    output_csv = pd.DataFrame([df_row], columns=["Design", "Time"])
                    output_csv.to_csv("History\\crudeoutput_final.csv", index=False)

            elif "ai" in str(next_action):
                print("Running AI assistance")
                self.TrafficManager.debug_mode = False
                # Set cars set if its empty
                if type(self.TrafficManager.test_cars) == list:
                    self.TrafficManager.set_test_set(self.states[-1], [1752, 1392], [2562, 412])
                #
                self.TrafficManager.generate_test_cases(self.TrafficManager.action_set)

                all_actions = self.TrafficManager.test_set
                current_state = all_actions[0] # This is the current state (root node of the decision tree)

                # Get kernel function
                self.surrogate_model = GraphBO(all_actions)
                #
                # # Generate a set of random numbers to be GP training data
                # x_train_index = list(random.sample(range(len(all_actions)), 16))
                # x_train = [all_actions[i] for i in x_train_index]
                #
                # # TODO: Fix Pooling (it throws an error in this context)
                # # pool = Pool()
                # # params = [(os.sep + "Networks\\Temp" + os.sep + str(x) + os.sep,1000,self.TrafficManager.test_cars, "") for x in x_train_index]
                # # for result in tqdm.tqdm(pool.imap(self.TrafficManager.runState, params), total=len(x_train)):
                # #     y_train.append(result)
                #
                # # Get y training data
                # y_train = []
                # for index in x_train_index:
                #     y_train.append(self.TrafficManager.runState(os.sep + "Networks\\Temp" + os.sep + str(index) + os.sep, 1000, self.TrafficManager.test_cars))
                # x_test = False
                # x_test_index = [5]
                #
                # while x_test == False:
                #     if x_test_index[0] in x_train_index:
                #         x_test_index = random.sample(range(len(all_actions)), 1)
                #     else:
                #         x_test = True
                # # Train the surrogate model on these data
                # y_prediction, sd = surrogate_model.GP_New_X(x_test_index, x_train_index, x_train, y_train)
                # y_test_true = []
                # for x in x_test_index:
                #     y_test_true.append(self.TrafficManager.runState(os.sep + "Networks\\Temp" + os.sep + str(x) + os.sep, 1000, self.TrafficManager.test_cars))
                # print("x_test = " + str(x_test_index))
                # print("y_test_true = " + str(y_test_true) + " and y_test_pred = " + str(y_prediction) + " with sd = " + str(sd))

                self.agent = Agent(self.beta_1, self.beta_2, self.p_omega, surrogate_model)

                h = str(all_actions[0]) # h will be an ordered list for the current state

                # Perform MCTS
                self.N = {}
                self.Na = {}
                self.Q = {}
                self.max_depth = 5

                i = 0
                while i < 5:
                    self.MCTS(h, current_state, d=1)
                    i += 1

                # # Return best action:
                # #UCB's of next states
                # UCB = []
                # #current state = h
                # potential_actions = self.get_next_actions(self.TrafficManager.test_set, current_action)
                # for action in potential_actions:
                #     index = str(h) + "a" + str(action)
                #     UCB.append(self.Q[index])
                #
                # print(UCB)
                # best_action_index = UCB.index(max(UCB))
                # print("The best action is: " + str(potential_actions[best_action_index]))

        return

    def utility(self, state, omega):
        # This function is used to return the reward function for a given state (using the traffic flow as a parameter)
        # I test using 1/x, since this favours lower traffic flows
        state_number = self.TrafficManager.action_set.index(state)
        traffic_flow = self.surrogate_model.GP_New_X()

        # TODO: Implement a reward function which uses omega
        u = 1 / traffic_flow
        return u
    def MCTS(self,h,s,d):
        # Temperature parameters
        c = 1
        gamma = 0.5

        # If we haven't been to this node before (with this history), set the count to 0
        if not str(h) in self.N:
            self.N[str(h)] = 0
        # Potential actions is a list containing roads which we can remove to get to the next state (all 1 road only)
        potential_actions = self.get_next_actions(self.TrafficManager.test_set, s)
        # If we haven't been to this node before, set Na and Q values to 0
        if self.N[str(h)] == 0:
            for action in potential_actions:
                index = str(h) + "a" + str(action)
                self.Na[index] = 0
                self.Q[index] = 0
        # Calculate the UCB for each of the potential actions
        UCB = []
        for action in potential_actions:
            index = str(h) + "a" + str(action)
            if self.N[str(h)] == 0 or self.Na[index] == 0:
                # We cant calculate log(0) or divide by 0
                UCB.append(self.Q[index])
            else:
                # We can calculate the true UCB value
                UCB.append(self.Q[index] + c * math.sqrt(math.log(self.N[str(h)]) / self.Na[index]))
        # print(UCB)
        # a_prime is the index of the optimum action from the potential_actions set.
        a_prime = UCB.index(min(UCB))
        # s_prime can be calculated with 100% accuracy since we are working with a graph problem
        s_prime = s + potential_actions[a_prime]
        h_prime = str(h) + "a" + str(potential_actions[a_prime])
        d_prime = d + 1
        index = str(h) + "a" + str(potential_actions[a_prime])
        # The reward is equal to the increase in utility (Which comes from the surrogate model)
        # r = utility(s_prime) - utility(s)
        # print(self.Na)

        if self.Na[index] == 0 or d == self.max_depth:
            q = gamma * self.est_value(h, s_prime,d_prime)
        else:
            q = gamma * self.MCTS(h_prime, s_prime, d_prime)

        self.N[str(h)] = self.N[str(h)] + 1

        self.Na[index] = self.Na[index] + 1
        self.Q[index] = self.Q[index] + ((q - self.Q[index]) / self.Na[index])
        print(self.Q)
        return q


    def est_value(self, h, s, d):
        # Predict the value for an unseen node
        # I will trial using the simulation directly initially.
        # Later, I will try to train a surrogate model (using bayesian optimisation + graph kernel)

        # Run the current state (s_prime)
        # print(s)
        index = 0
        temp_s = set(s)
        # print(temp_s)
        index = 0
        i = 0
        for value in self.TrafficManager.test_set:
            if set(value) == set(temp_s):
                index = i
            i += 1
        # index = self.TrafficManager.test_set.index(temp_s)

        # Run simulation for the network at index = {index}
        # TODO surrogate model
        result = self.TrafficManager.runState("\\Networks\\Temp\\" + str(index) + "\\", 2000, self.TrafficManager.test_cars)
        # print("The output of state " + str(index) + " is equal to " + str(result))
        return result
    def get_next_actions(self, all_actions, current_action):

        next_actions = []
        print("The current action is:")
        print(current_action)

       # print("The possible next states are:")
        for action in all_actions:
            if set(current_action) <= set(action):
                if len(action) == len(current_action) + 1:
                    next_actions.append([x for x in action if x not in current_action])

        #print(next_actions)
        return next_actions



if __name__ == '__main__':
    Traffic = DesignerController("TrafficProblem", "./TrafficProblem/Networks/", True,1,1,1)

