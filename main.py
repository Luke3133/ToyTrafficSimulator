import numpy as np
import os, sys
import time
from multiprocessing import Pool
import tqdm
import pandas as pd
import shutil
from TrafficProblem.traffic import TrafficProblemManager
from itertools import chain

dir_path = os.path.dirname(os.path.realpath(__file__))

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

    def __init__(self, problem_files, state_files, debug_mode):
        self.problemfiles = problem_files
        self.statefiles = state_files

        if self.problemfiles == "TrafficProblem":
            self.TrafficManager = TrafficProblemManager(debug_mode)
            self.states.append("\\Networks\\Original\\")

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
            elif "crude" in str(next_action):
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
            elif "set" in str(next_action):
                self.TrafficManager.set_test_set(self.states[-1], [2562, 412], [1752, 1392])
                self.TrafficManager.generate_test_cases(self.TrafficManager.action_set)

            elif "next" in str(next_action):
                test_vehicles = self.TrafficManager.test_cars
                test_streets = self.TrafficManager.test_set
                test_streets_vector = list(range(0,len(test_streets)))

                pool = Pool()
                result_list_tqdm = []
                for result in tqdm.tqdm(pool.imap_unordered(self.TrafficManager.run_network_reduction_function, test_streets_vector), total=len(test_streets)):
                    result_list_tqdm.append(result)
                result = pd.DataFrame(result_list_tqdm)
                print(result)
                min_result = min(result)
                min_index = result.index(min_result)
                print("The minimum value is " + min_result + " located at " + min_index)





                # crude_output = []
                # test_case_counter = 0
                # self.TrafficManager.debug_mode = False
                #
                # for test_cases in test_streets:
                #     # Make a directory to hold the networks
                #     print(str((test_case_counter / len(test_streets)) * 100) + "%")
                #     if not test_cases:
                #         # # this is the case where we have the original network (no changes)
                #         result = self.TrafficManager.runState("\\Networks\\Temp\\" + str(test_case_counter) + "\\", 2000, test_vehicles, self.TrafficManager.test_street)
                #         crude_output.append(result)
                #     else:
                #         # print("Running " + str(test_case_counter))
                #         # this is the case where we make some changes
                #         self.TrafficManager.runAction(test_cases, "\\Networks\\Original\\", "\\Networks\\Temp\\" + str(test_case_counter) + "\\")
                #         result = self.TrafficManager.runState("\\Networks\\Temp\\" + str(test_case_counter) + "\\", 2000, test_vehicles, self.TrafficManager.test_street)
                #         crude_output.append(result)
                #     test_case_counter += 1
                # min_output = min(crude_output)
                # min_index = crude_output.index(min_output)
                # data = {
                #     "Design": [min_index],
                #     "Time": [min_output]
                # }
                # df_row = pd.DataFrame(data)
                # print("Min row = " + str(df_row))
                # history = pd.read_csv("History\\crudeoutput_final.csv")
                # history = pd.concat([history, df_row])
                # history.to_csv("History\\crudeoutput_final.csv",index=False)

        return

    def run_next_iteration(self, best_action):

        # Run an action / update the state (action type value)
        self.actions.append("remove " + best_action)
        print("remove " + best_action)
        # Set the new state for the action to take us to
        if self.states[-1] == "\\Networks\\Original\\":
            self.states.append("\\Networks\\1\\")
        else:
            last_state = int(str(self.states[-1]).replace("\\Networks\\", "").replace("\\", ""))
            self.states.append("\\Networks\\" + str(last_state + 1) + "\\")
        self.TrafficManager.runAction(self.actions[-1], self.states[-2], self.states[-1])

        print(self.states[-1])
        self.TrafficManager.convert_network_to_matrix(self.states[-1])

        # Run crude
        self.TrafficManager.debug_mode = False
        network_matrix = self.TrafficManager.run_network_reduction_step(self.states[-1])
        pool = Pool()
        result_list_tqdm = []
        for result in tqdm.tqdm(
                pool.imap_unordered(self.TrafficManager.run_network_reduction_function, network_matrix['Edge ID']),
                total=len(network_matrix['Edge ID'])):
            result_list_tqdm.append(result)
        result = pd.DataFrame(result_list_tqdm)
        last_state = int(str(self.states[-1]).replace("\\Networks\\", "").replace("\\", ""))
        result.to_csv("Results" + str(last_state + 1) + ".csv", index=False)
        result = pd.read_csv("Results" + str(last_state + 1) + ".csv")
        best = list(result.loc[result['1'] == result['1'].min()]['0'])
        print("The best action is: " + best[0])

        # Analyze
        df = pd.read_csv("History\\PastResults.csv")
        newdf = df.append(list(zip([best[0]], [float(result['1'].min())])))
        newdf.to_csv("History\\PastResults.csv")
        shutil.rmtree(dir_path + "\\TrafficProblem\\Networks\\Temp\\")


if __name__ == '__main__':
    Traffic = DesignerController("TrafficProblem", "./TrafficProblem/Networks/", True)
