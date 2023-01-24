import numpy as np
import os, sys
import time
import eel
from TrafficProblem.traffic import TrafficProblemManager


class RecommenderController:

    states = []
    actions = []
    rewards = []
    recommended_actions = []
    problemfiles = ""
    htmlcontroller = ""

    def __init__(self, problem_files, state_files, debug_mode, website_url):
        self.problemfiles = problem_files
        self.statefiles = state_files
        self.htmlcontroller = website_url
        eel.init(self.htmlcontroller)









        if self.problemfiles == "TrafficProblem":
            self.TrafficManager = TrafficProblemManager(debug_mode)
            self.states.append("./Networks/Original/")

        self.actionManager()

    def actionManager(self):
        finished = False
        while not finished:
            # Await an action by the user
            next_action = input("Select next action")
            # eel.start('index.html')
            # @eel.expose
            # def run(value):
            #     print(value)
            #     self.TrafficManager.runState(self.states[-1], int(value))

            if str(next_action) == "end":
                finished = True
            elif str(next_action) == "history":
                # self.print_history()
                print("History")
            elif "run" in str(next_action):
                runparameter = str(next_action).replace("run","")  # runparameter can be blank depending on scenario!
                print(runparameter)
                if " " in runparameter:
                    runparameter = int(runparameter)
                else:
                    runparameter = -1
                self.TrafficManager.runState(self.states[-1], runparameter)
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


Traffic = RecommenderController("TrafficProblem", "./TrafficProblem/Networks/", True, "./Website/")
