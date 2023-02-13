import numpy as np
import os, sys
import time
from multiprocessing import Pool
from TrafficProblem.traffic import TrafficProblemManager


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
    htmlcontroller = ""

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
                self.print_history()
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
                self.TrafficManager.runAction(self.actions[-1], self.states[-2], self.states[-1])


                # self.new_turn(int(next_action), self.sta te[-1])

            elif "convert" in str(next_action):
                # Run an action / update the state (action type value)

                self.TrafficManager.convert_network_to_matrix(self.states[-1])

            elif "crude" in str(next_action):
                network_matrix = self.TrafficManager.run_network_reduction_step(self.states[-1])
                # with Pool() as pool:
                #     Result = pool.map(self.TrafficManager.run_network_reduction_function, network_matrix['Edge ID'])

                #(Result)
        return(10)

    def print_history(self):
        print("The states history is : " + str(self.states))
        print("The action history is : " + str(self.actions))
        print("The reward history is : " + str(self.rewards))

if __name__ == '__main__':
    Traffic = DesignerController("TrafficProblem", "./TrafficProblem/Networks/", True)

class RecommenderController:
    # This class is used to represent the new method of iterating on sequential designs. The user can run the
    # state, look at the output and choose an action. During this process, the AI will make recommendations as to
    # which state the user should pick. The AI will infer the users goals and how to achieve them in the simulator.
    # This class can also be used in my new method where a surrogate model is used. We do this by inputting a surrogate
    # model during instantiating the class.

    states = []
    actions = []
    rewards = []
    recommended_actions = []
    omega = []
    psi = []
    theta = []
    gamma = 0
    problemfiles = ""
    htmlcontroller = ""
    surrogate = ""
    using_surrogate = False
    reward_function = []
    

    def __init__(self, problem_files, state_files, debug_mode, surrogate_model, p0s, p0omega, p0theta, p0psi):
        self.problemfiles = problem_files
        self.statefiles = state_files
        self.omega.append(p0omega)
        self.psi.append(p0psi)
        self.theta.append(p0theta)


        if self.problemfiles == "TrafficProblem":
            self.TrafficManager = TrafficProblemManager(debug_mode)
            self.states.append("./Networks/Original/")

        if surrogate_model != "NONE":
            using_surrogate = True

        self.actionManager()

    def actionManager(self):
        finished = False
        while not finished:
            # Await an action by the user
            next_action = input("Select next action")

            if str(next_action) == "end":
                finished = True
            elif str(next_action) == "history":
                self.print_history()
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
                if self.states[-1] == "./Networks/Original/":
                    self.states.append("./Networks/1/")
                else:
                    last_state = int(str(self.states[-1]).replace("./Networks/","").replace("/",""))
                    self.states.append("./Networks/" + str(last_state + 1) + "/")
                self.TrafficManager.runAction(self.actions[-1], self.states[-2], self.states[-1])


                # self.new_turn(int(next_action), self.state[-1])
        return(10)

    def print_history(self):
        print("The states history is : " + str(self.states))
        print("The action history is : " + str(self.actions))
        print("The reward history is : " + str(self.rewards))


#Traffic = RecommenderController("TrafficProblem", "./TrafficProblem/Networks/", True, "NONE")