# This class is the boltzman rational agent for the user model
import math
import numpy as np
class Agent:
    beta_1 = 0
    beta_2 = 0
    p_omega = 0

    def __init__(self, beta_1, beta_2, p_omega, Surrogate, prior = "Uniform"):
        print("Starting up agent")
        self.beta_1 = beta_1
        self.beta_2 = beta_2
        self.action_prior = prior
        self.p_omega = p_omega
        self.surrogate = Surrogate

    def prior_actions(self, action, action_set):

        if self.action_prior == "Uniform":
            if len(action) == 1:
                # Prior probability for a single action
                prior = 1 / len(action_set)
                return prior
            else:
                # Return the vector of prior probabilities for the actions
                prior = 1 / len(action_set)
                prior = np.repeat(prior, len(action))
                return prior

    def p_action_given_recommendation(self, action, action_set, recommended_action, q_values):
        # This function calculates the probability of the user model picking an action {action} given a recommendation
        # {recommended_action} with q-values {q_values} and an action set A = {action_set}

        if not q_values:
            # The q_values have not been set, so we should set them
            print("Set q-values")


        # Calculate the probability of the user model picking an action
        p_action_numerator = np.multiply(self.prior_actions(action_set, action_set), np.exp(self.beta_1 * q_values))
        p_action_denominator = sum(np.multiply(self.prior_actions(action_set, action_set), np.exp(np.multiply(q_values, self.beta_1))))
        p_action = p_action_numerator / p_action_denominator

        # Calculate the probability of the user model switching from {action} to {recommended_action}

        p_action_switch_numerator = np.exp(self.beta_2 * (0 - (q_values - q_values[recommended_action])))
        p_action_switch_denominator = 1 + np.exp(self.beta_2 * (0 - (q_values - q_values[recommended_action])))
        p_action_switch = np.divide(p_action_switch_numerator, p_action_switch_denominator)

        p_switched = sum(np.multiply(p_action,p_action_switch)) # TODO: Think about this!!!

        # Calculate the probability of the user model choosing action {action} given recommendation {recommended_action}

        p_switch = np.multiply((0 - (p_action_switch - 1)), p_action)

        return p_switch

    def reward(self, s, s_prime):
        r = self.utility(s_prime) - self.utility(s)
        return r

    def utility(self, state):
        # Get traffic levels for this state and multiply by omega
        output = 0
        u = 0
        return u
