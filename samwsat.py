#!/usr/bin/python3

# David Omrai
# SA metaheuristic
# 01.01.2024

import sys, getopt
import random
from datetime import datetime
import math
import numpy
import copy
import time
import logging

# opt_vals = {
#   "wuf50-01": 36854,
#   "wuf50-02": 16683,
#   "wuf50-03": 61079
# }

# Class groups all necessary information about the evaluation
class EvalInfo:
  def __init__(self, eval, weight, sat_num, unsat_num):
    self.eval = eval
    self.weight = weight
    self.sat = unsat_num == 0
    self.sat_num = sat_num
    self.unsat_num = unsat_num

# Class represents the Simulated Annealing heuristc
class SimAnn:
  def __init__(self, argv = None):
    # Initialize the random
    random.seed(datetime.now().timestamp())
    # Empty names of files
    self.instance_name = ""
    self.ifile_name = ""
    self.sol_file_name = ""
    
    # Algorithm params
    self.init_temp = 50.0 # todo
    self.final_temp = 0.05
    self.iter_num = 1000 # todo
    self.cool_factor = 0.95 # todo
    
    # Results
    self.all_sat = list()
    self.all_unsat = list()
    self.all_weights = list()
    self.all_weights_iter = list()
    self.res_weight = 0
    self.res_state = 0
    self.res_steps = 0
    self.duration = 0
    
    # Instance params
    self.formula = list()
    self.weights = list()
    self.var_num = 0
    self.clause_num = 0
    
    self.log = logging.getLogger(__name__)
    self.log.setLevel(logging.INFO)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    self.log.addHandler(ch)
    
  
    # Load the input data
    if (argv != None):
      self.load_input(argv)
      self.load_formula(self.ifile_name)
      
  # Init temp setter
  def set_init_temp(self, init_temp):
    self.init_temp = init_temp
    
  # Final temp setter
  def set_final_temp(self, final_temp):
    self.final_temp = final_temp
  
  # Iter temp setter
  def set_iter_num(self, iter_num):
    self.iter_num = iter_num
    
  # Cool factor setter
  def set_cool_factor(self, cool_factor):
    self.cool_factor = cool_factor
    
  # Instance file setter
  def set_input_file(self, file_name):
    self.ifile_name = file_name
    self.load_formula(file_name)
    
  # Method loads the command input
  def load_input(self, argv):
    # CMD command format
    command_format = "samwsat.py -i <inputfile> -t <inittemp> -n <iternum> -c <coolfactor>"
    # Try to read the command line
    try:
      opts, args = getopt.getopt(argv, "hi:t:n:c:")
    except getopt.GetoptError:
      self.log.warning(command_format)
      sys.exit(2)
    
    # Command format is incorrect
    if not opts:
      self.log.warning(command_format)
      sys.exit(2)
    
    # Command format is correct
    for opt, arg in opts:
      if opt == '-h':
        self.log.warning(command_format)
        sys.exit(2)
      elif opt in ("-i"):
        self.ifile_name = arg
      elif opt in ("-t"):
        self.init_temp = int(arg)
      elif opt in ("-n"):
        self.iter_num = int(arg)
      elif opt in ("-c"):
        self.cool_factor = float(arg)
        
  # Reading the data from given file
  def read_file(self, file_name):
    # Open the file
    f = open(file_name, "r")
    return f.readlines()
  
  # Getting the formula from the file data
  def get_formula(self, file_lines):
    file_info_len = 11
    if (len(file_lines) < file_info_len ):
      self.log.warning("Error: not valid input file")
      sys.exit(2)

    formula = []
    weights = []
    try:
      # read the information
      self.instance_name = file_lines[7].strip().split()[3]
      ins_info = file_lines[8].strip().split()
      var_num = int(ins_info[2])
      claus_num = int(ins_info[3])
      
      # get the claus
      for line in file_lines[file_info_len:]:
        var_array = [int(num) for num in line.strip().split()[:-1]]
        formula.append(var_array)

      # test the number of claus
      if claus_num != len(formula):
        raise ValueError("Error: Bad file data format")
      
      # get the literals weights
      for weight in file_lines[9].strip().split()[1:-1]:
        weights.append(int(weight))
        
      # test the number of literals 
      if var_num != len(weights):
        raise ValueError("Error: Bad file data format")
    except:
      self.log.warning("Error: can't load data from file")
      raise

    return formula, weights
  
  def load_formula(self, file_name):

    file_lines = self.read_file(file_name)
    self.formula, self.weights = self.get_formula(file_lines)
    self.var_num = len(self.weights)
    self.clause_num = len(self.formula)
    
  # ------------------------------------------------------------
  
  # With given setting of varialbe x
  # the function evaluates clause
  # and returns if it's satisfied or not
  def evaluate_clause(self, clause, truth_eval):
    for c_x in clause:
      if c_x > 0 and truth_eval[abs(c_x)-1] == 1:
        return True
      if c_x < 0 and truth_eval[abs(c_x)-1] == 0:
        return True
    return False
  
  # Evaluate the formula
  def evaluate_formula(self, truth_eval):
    sat_num = 0
    unsat_num = 0
    for clause in self.formula:
      if self.evaluate_clause(clause, truth_eval) == False:
        unsat_num += 1
      else:
        sat_num += 1
    return sat_num, unsat_num
  
  # Random evaluation
  def get_random_evaluation(self):
    init_eval = list()
    for _ in range(self.var_num):
      init_eval.append(random.randint(0, 1))
    return init_eval
  
  # Random neighbour (one change)
  def get_random_neighbour(self, state):
    rand_index = random.randint(0, self.var_num - 1)
    state[rand_index] = (state[rand_index] + 1) % 2
    return state
  
  # Random neighbour (change random number of variables)
  def get_random_neighbour_1(self, state):
    for i in range(len(state)):
      state[i] = (state[i] + random.randint(0, 1)) % 2
    return state
  
  def get_random_neighbour_2(self, state):
    for _ in range(int(len(state)/4)):
      rand_index = random.randint(0, self.var_num - 1)
      state[rand_index] = (state[rand_index] + 1) % 2
    return state
  
  def get_random_neighbour_3(self, state, t):
    one_bit_prob = math.exp(-t)
    
    if random.randint(0, 1) < one_bit_prob:
      return self.get_random_neighbour(state)
    else:
      return self.get_random_neighbour_2(state)
  
  # Combination of the two previous
  # def get_random_neighbour_2(self, state):
    
    
  # Method returns the weight of formula evaluation
  def get_weight(self, state):
    state_weight = 0
    for i in range(len(state)):
      state_weight += self.weights[i] * state[i]
    return state_weight
  
  def get_sat_clause_weight(self, state):
    state_weight = 0
    
    for clause in self.formula:
      if self.evaluate_clause(clause, state) == True:
        for c_x in clause:
          if c_x > 0 and state[abs(c_x)-1] == 1:
            state_weight += self.weights[abs(c_x)-1]
            
    return state_weight
    
  def repair_state(self, state):
    # While the state is not feasible try to find new random neighbour
    while self.evaluate_formula(state) == False:
      state = self.get_random_neighbour(state)
  
  def accept_worse(self, curr_state, old_state, t):
    if t == 0:
      return False
    # sigma -> 0, pnew -> 1 - little bad
    # sigma -> inf, pnew-> 0 - big bad
    # T -> 0, pnew -> 0 - under a small temp, small prob to little worse (intenzification)
    # T -> inf, pnew -> 1 - under big temp, even a big bad (diverzification)
    eps =  old_state.sat_num - curr_state.sat_num
    return random.uniform(0, 1) < math.exp(- (eps) / t)
  
  def state_to_string(self, state):
    state_str = ""
    for i in range(len(state)):
      state_str += str((-(i+1))*((-1)**state[i])) + " "
    return state_str
  
  def string_to_state(self, state_str):
    state = list()
    for str_num in state_str.strip().split():
      if int(str_num) > 0:
        state.append(1)
      else:
        state.append(0)
    return state
  
  # Method decides whether the new state is better than
  # the old one or not
  def is_better(self, new_state, old_state):    
    if (new_state.sat == True and old_state.sat == True):
      return new_state.weight > old_state.weight
    if (new_state.sat == True and old_state.sat == False):
      return True
    if (new_state.sat == False and old_state.sat == False):
      return new_state.sat_num > old_state.sat_num
    return False
  
  # Method decides whether the new state is better
  # then the previous best
  def is_new_best(
      self, new_state, top_state):
    if len(top_state.eval) == 0:
      return True
    
    return self.is_better(new_state, top_state)
    

  # Simulated annealing algorithm for mwsat
  def sim_ann(self):
    steps_count = 0
    t = self.init_temp
    res_num = 0
    
    top_state = EvalInfo(list(), 0, 0, 0)
    
    # Initialize the first state
    curr_eval = self.get_random_evaluation()
    curr_sat_num, curr_unsat_num = self.evaluate_formula(curr_eval)
    curr_weight = self.get_weight(curr_eval)
    
    curr_state = EvalInfo(
      curr_eval, curr_weight, curr_sat_num, curr_unsat_num)
    
    # start the annealing
    while t > self.final_temp and steps_count < self.iter_num:      
      new_eval = self.get_random_neighbour_3(copy.deepcopy(curr_state.eval), t)
      # self.repair_state(new_state) - way too complex
      new_weight = self.get_weight(new_eval)
      new_sat_num, new_unsat_num = self.evaluate_formula(new_eval)
      
      new_state = EvalInfo(new_eval, new_weight, new_sat_num, new_unsat_num)
      
      # Store best weight and state
      if self.is_new_best(new_state, top_state):
        top_state = new_state
        # prevent the possible changes
        top_state.eval = copy.deepcopy(top_state.eval)
      
      # Decide wheter to accept or not
      if self.is_better(new_state, curr_state) or (self.accept_worse(new_state, curr_state, t)):
        curr_state = new_state
        # old debug
        # self.all_sat.append(curr_state.sat_num)
        # self.all_unsat.append(curr_state.unsat_num)
        # self.all_weights.append(curr_state.weight)
        # self.all_weights_iter.append(steps_count)
        # debug info - critical output to filter the results
        self.log.critical("{} {} {} {} {} {}".format(
          steps_count, t, int(curr_state.sat), curr_state.sat_num, curr_state.unsat_num, curr_state.weight))

      t = t * self.cool_factor
      # Stop if the temperature reaches the minimum
      if t < self.final_temp and top_state.sat == 0 and res_num < 2:
        t = self.init_temp
        res_num += 1
        
      steps_count += 1
          
    return top_state, steps_count 
  
  # Method starts the algorithm
  def run(self):
    # Start the timer
    start_time = time.time()
    top_state, steps_count = self.sim_ann()
    duration = time.time() - start_time
    
    self.res_weight = top_state.weight
    self.res_state = top_state.eval
    self.res_steps = steps_count
    self.duration = duration
    # Print the result     
    # if defined opt values, uncomment this (definition is at the top of this file)
    # print("{} {} {} {} {} {} {}".format(
    #   int(top_state.sat), top_state.sat_num, top_state.unsat_num, top_state.weight, 
    #   opt_vals[str(self.ifile_name.split("/")[-1].split(".")[0])], steps_count, duration))
    
    print("{} {} {} {} {} {}".format(
      int(top_state.sat), top_state.sat_num, top_state.unsat_num, top_state.weight, 
      steps_count, duration))
    

if __name__ == "__main__":
  samwsat = SimAnn(sys.argv[1:]) #(["-i", "data/wuf20-71/wuf20-71-M/wuf20-01000.mwcnf", "-o", "output.txt"])#
  # run algorithm
  samwsat.run()
  