import csv
import json
import pulp
import numpy as np
import pandas as pd

def save_batteries_to_json(battery_dict, file_path):
    """
    This function will save the battery object dictionary to a json file that is specified. The json file structure will be
    a large dict with keys equal to the barcode of the battery and the value is a dictionary which is a battery objects
    dictionary. i.e. {"0000A": {barcode:"0000A", under_diag: False, etc}, "0000B": etc}.

    Args:
    :param battery_list: {"barcode": Battery}
        This is a dictionary of Battery data objects as values and their barcode as keys. It should have all the battery 
        data objects that need to be stored.
    :param: file_path: str
        This is a filepath to the json file that should be saved. If there is anything else here it will be overwritten
    
    Returns: None
    """
    json_battery_dict = {}
    for key in battery_dict.keys():
        json_battery_dict[key] = battery_dict[key].__dict__
        
    #write in to the json file
    with open(file_path, 'w') as f:
        json.dump(json_battery_dict, f, indent=2)


def save_diag_chambers_to_json(diag_chamber_dict, file_path):
    """
    This function will save the diagnostic chambers to the json file that is specified. The json file structure will be
    a dict with keys equal to the names of the diagnostic chambers and the value is a dictionary with all the data about the 
    current state of the diagnostic chamber. 

    Args:
    :param battery_list: {"Chamber_name": DiagnosticChamber}
        This is a dictionary of DiagnosticChamber data objects as values and their names as keys. It should have all the 
        DiagnosticChamber data objects that need to be stored.
    :param: file_path: str
        This is a filepath to the json file that should be saved. If there is anything else here it will be overwritten.
    
    Returns: None
    """

    json_diag_chamber_dict = {}
    for key in diag_chamber_dict.keys():
        json_diag_chamber_dict[key] = diag_chamber_dict[key].__dict__

    #write in to the json file
    with open(file_path, 'w') as f:
        json.dump(json_diag_chamber_dict, f, indent=2)

def save_temp_chambers_to_json(temp_chamber_dict, file_path):
    """
    This function will save the temperature chambers to the json file that is specified. The json file structure will be
    a dict with keys equal to the names of the temperature chambers and the value is a dictionary with all the data about temperature
    and batteries stored in a temperature chamber.

    Args:
    :param battery_list: {"Chamber_name": TemperatureChamber}
        This is a dictionary of TemperatureChamber data objects as values and their names as keys. It should have all the 
        TemperatureChamber data objects that need to be stored.
    :param: file_path: str
        This is a filepath to the json file that should be saved. If there is anything else here it will be overwritten.
    
    Returns: None
    """

    json_temp_chamber_dict = {}
    for key in temp_chamber_dict.keys():
        json_temp_chamber_dict[key] = temp_chamber_dict[key].__dict__

    #write in to the json file
    with open(file_path, 'w') as f:
        json.dump(json_temp_chamber_dict, f, indent=2)


def auto_assign_batteries(battery_obj_dict, temp_chamb_obj_dict, verbose=False):
    """
    This will take the unassigned batteries and assign them to temperature chambers based on temperature.
    There is no metric for when a chamber is too full so it will just assign it to whicherever
    chamber appears first. The batteries current location and storage location will be updated, and the 
    temperature chamber's battery_list will be updated to reflect adding these batteries to the storage 
    temeprature chambers. 

    Args:
    :param battery_obj_dict: {"barcode": Battery, ...}
        Dictionary with keys as the barcode and values as Battery data objects. 
    :param temp_chamb_obj_dict: {"name": TemperatureChamber, ...}
        Dictionary with keys as the chamber name and values as TemperatureChamber data objects. 

    Returns: None
    """

    #group batteries that need to assigned by their temperatures
    batteries_to_assign_dict = {}
    for barcode in battery_obj_dict.keys():
        battery_obj = battery_obj_dict[barcode]

        #unassigned cells will be included
        if battery_obj.storage_location == "Unassigned":
            temp = battery_obj.temperature
            # Add the barcode to the list for the corresponding temperature
            if temp in batteries_to_assign_dict:
                batteries_to_assign_dict[temp].append(barcode)
            else:
                batteries_to_assign_dict[temp] = [barcode]

    #assign the batteries to temperature chambers based on their temperature
    for battery_temp in batteries_to_assign_dict.keys():

        batteries_assigned = False
        for temp_chamb_name in temp_chamb_obj_dict.keys():
            temp_chamb_obj = temp_chamb_obj_dict[temp_chamb_name]
            
            if battery_temp==temp_chamb_obj.temperature:
                #update batteries to be in the temperature chamber
                for barcode in batteries_to_assign_dict[battery_temp]:
                    temp_chamb_obj.assign_battery(battery_obj_dict[barcode])
                    if verbose:
                        print("{} -> {}".format(barcode, temp_chamb_obj.name))
                batteries_assigned = True
                #Once assigned leave the loop so we don't assign again
                break
        
        if not batteries_assigned:
            raise Exception("{} does not match any temperature chamber".format(battery_temp))
    print("All Batteries Assigned")
    return None

def determine_optimal_schedule(interval_list, chamber_capacity, max_weeks, objective="Min Average Start", time_limit=60, verbose=False):
    """
    This determines the optimal scheduling of batteries given a battery list by formulating it as a integer
    linear program (ILP) using the pulp library. For details of the implementation see docs. 

    Todo: 
    - Does not account that certain batteries can only be loaded on certain channels if they have certain
    form factors
    - Batteries that have the same interval there is no benefit to switching them in the optimization. If 
        this logic can be encoded, potentially saves on computation time. 
    - Could maybe give suggestions if optimal schedule can not be found?
    - different optimization objectives for things like chamber utilization such as optimizing a more even
        chamber utilization each week so there is more leway.

    Args:
    @interval_list: [int]
        List intervals the batteries need to be tested at
    @chamber_capacity: int
        Number of batteries that can be tested in a diagnostic chamber
    @max_weeks: int
        The time to simulate out for. Time to solve will increase drastically if this gets very large
    @objective: str, default="Min Average Start
        Supported objective functions. 
        "Min Average Start": corresponds to minimizing the sum of all the start times across all batteries
        "Min Max Start": corresponds to minimizng the maximum time a battery is started
    @verbose: Boolean, default=False
        If true this will also print the output log of the solver
    @time_limit: float, default=60
        Time limit of the solver in seconds.

    Returns: [[Boolean]]
        2D Boolean Schedule Matrix row i corresponds to the index of Battery in battery_list, column corresponds
        to testing slot week j. If value is 1, then the battery is being tested during that testing week/slot, if 0 
        it is not being tested.
    """


    #Get interval list of batteries
    n_batteries = len(interval_list)

    # Create the ILP Problem
    problem = pulp.LpProblem("Battery_Scheduling_Problem", pulp.LpMinimize)

    # Generate decision variables
    #Columns (j) is week, rows (i) is the battery
    #Binary matrix 1 for anytime a battery is being tested
    x = [[pulp.LpVariable(f"x_{i}_{j}", cat="Binary") for j in range(max_weeks)] for i in range(n_batteries)]
    #Binary matrix, only 1 wherever a battery is tested for the first time
    s = [[pulp.LpVariable(f"s_{i}_{j}", cat="Binary") for j in range(max_weeks)] for i in range(n_batteries)]

    # Auxiliary variable to track the latest start time of a battery
    t_max = pulp.LpVariable("t_max", lowBound=0, cat="Integer")
    
    # Objective Function: Minimize t_max (latest start week)
    problem += t_max, "Minimize_latest_start_week"


    # Constraints

    # 1. Periodicity constraint: Each battery must be tested periodically after the first test
    for i in range(n_batteries):
        interval = interval_list[i]
        for start_week in range(max_weeks):
            for future_week in range(start_week, max_weeks, interval):
                problem += x[i][future_week] >= s[i][start_week]


    # 2. Chamber capacity constraint: No more than `chamber_capacity` batteries can be tested in any week
    for j in range(max_weeks):
        problem += pulp.lpSum(x[i][j] for i in range(n_batteries)) <= chamber_capacity

    # 3. Batteries scheduled constraint: batteries must be started
    # Note: think if there is any issue where it will schedule a battery right at the end so it doesn't run in to periodicity
    # issues.
    for i in range(n_batteries):
        problem += pulp.lpSum(s[i][j] for j in range(max_weeks)) >= 1

    # 4. Determine constraints on the objective function value
    if objective == "Min Max Start":
        for i in range(n_batteries):
            for j in range(max_weeks):
                #highest value of j*first_start_matrix[i][j] is the only constraint that matters
                problem += t_max >= j * s[i][j]
    elif objective == "Min Average Start":
        #Minimizing sum of all start weeks is same as minimizing average start week
        problem += t_max >= pulp.lpSum(((j * s[i][j])  for j in range(max_weeks)) for i in range(n_batteries))


    # Solve the ILP problem
    if verbose:
        solver = pulp.PULP_CBC_CMD(msg=1, timeLimit=time_limit)
    else:
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
    status = problem.solve(solver)

    # Check the status of the solution
    if status == pulp.LpStatusOptimal:
        print("Optimal solution found")
        schedule_matrix = unpack_pulp_schedule_matrix(x)
        return schedule_matrix
    elif status == pulp.LpStatusNotSolved:
        raise Exception("Solver did not finish, no feasible solution found")
    elif status == pulp.LpStatusInfeasible:
        raise Exception("Problem is infeasible")
    elif status == pulp.LpStatusUnbounded:
        raise Exception("Problem is unbounded")
    else:
        print("Unknown issues present")
        schedule_matrix = unpack_pulp_schedule_matrix(x)
        return schedule_matrix


def unpack_pulp_schedule_matrix(pulp_matrix):
    """
    Given a pulp data matrix this will instead return a numpy array of the actual values

    Args:
    pulp_matrix: [[pulp.pulp.LpVariable]]
        List of list of pulp LpVariable objects. First list is battery index, second list is 
        time. The values of the variables should just be numbers.

    Returns:
    schedule_matrix: np.array([[]])
        2D numpy array with unpacked values from the pulp_matrix.
    """

    n_batteries = len(pulp_matrix)
    max_weeks = len(pulp_matrix[0])
    schedule_matrix = np.zeros((n_batteries, max_weeks))

    for i in range(n_batteries):
        for j in range(max_weeks):
            schedule_matrix[i][j] = pulp_matrix[i][j].value()

    return schedule_matrix

def get_latest_start_time(schedule_matrix):
    """
    Args: 
    schedule_matrix: np.array([[]])
        2D binary numpy array. Columns are weeks, rows are batteries. 1 if battery 
        being tested 0 if not.

    Returns: Max start week present in the matrix
    """
    
    return np.max((schedule_matrix==1).argmax(axis=1))

def get_average_start_time(schedule_matrix):
    """
    Args: 
    schedule_matrix: np.array([[]])
        2D binary numpy array. Columns are weeks, rows are batteries. 1 if battery 
        being tested 0 if not.

    Returns: Mean start week
    """
    
    return np.mean((schedule_matrix==1).argmax(axis=1))

def print_schedule(schedule_matrix, battery_list, chamber_capacity):
    """
    This prints out the chamber capacity weekly as well as the batteries that are tested.

    Args: 
    schedule_matrix: np.array([[]])
        2D binary numpy array. Columns are weeks, rows are batteries. 1 if battery 
        being tested 0 if not.
    battery_list: [Battery]
        List of batteries where the index corresponds to the row of the schedule_matrix
    chamber_capacity: int
        The capacity of the chambers that are used. This will be used to show how much of the chamber
        is being used.

    Returns: None
    """
    n_batteries, total_weeks = schedule_matrix.shape
    total_batteries_tested_weekly = np.sum(schedule_matrix, axis=0)
    for current_week in range(total_weeks):
        print("Week {:.0f} {:.0f}/{:.0f}: ".format(current_week, total_batteries_tested_weekly[current_week], chamber_capacity))
        for battery_idx in range(n_batteries):
            if schedule_matrix[battery_idx, current_week]==1 :
                battery=battery_list[battery_idx]
                print(f"-Battery {battery.barcode} with Interval {battery.interval}")

    return None


def print_first_start_time(schedule_matrix, battery_list):
    """
    This function will print just prints whenever the batteries are first started.

    Args:
    schedule_matrix: np.array([[]])
        2D binary numpy array. Columns are weeks, rows are batteries. 1 if battery 
        being tested 0 if not.
    battery_list: [Battery]
        List of batteries where the index corresponds to the row of the schedule_matrix

    Returns: None
    """

    n_batteries, total_weeks = schedule_matrix.shape
    total_batteries_tested_weekly = np.sum(schedule_matrix, axis=0)
    already_printed = [False]*n_batteries
    for current_week in range(total_weeks):
        print("Week {:.0f}: ".format(current_week))
        for battery_idx in range(n_batteries):
            if (schedule_matrix[battery_idx, current_week]==1) and (not already_printed[battery_idx]) :
                battery=battery_list[battery_idx]
                already_printed[battery_idx] = True
                print(f"-Battery {battery.barcode} with Interval {battery.interval} Started")

    return None

def get_panda_df_optimal_schedule(battery_obj_dict, diag_chamb_obj_dict, buffer=0, max_weeks = 7, time_limit=10, objective="Min Average Start"):
    """
    This is mostly a wrapper function for the actual pulp optimization. This will return 
    the schedule matrix in a form with index labels and column names
    
    TODO: Finish the documentation

    Args:
    max_weeks(int): Max weeks to simulate out until
    time_limit(int): time limit for how long to find a solution. If not found in this time conclude no feasible solution

    returns: schedule_df(pd.DataFrame) index is the barcode, column is week/testing interval number. 1 means to test, 0 means to not test
    """

    #get chamber capacity
    chamber_capacity = 0
    for diag_chamb_name in diag_chamb_obj_dict.keys():
        chamber_capacity += len(diag_chamb_obj_dict[diag_chamb_name].channels["channel"])

    chamber_capacity -= buffer

    interval_list = [battery_obj_dict[barcode].diagnostic_frequency for barcode in battery_obj_dict]

    #Get optimal schedule matrix
    schedule_matrix = determine_optimal_schedule(interval_list, chamber_capacity, max_weeks, objective=objective, verbose=False, time_limit=time_limit)
    #Print values you may want to check
    t_max = get_latest_start_time(schedule_matrix)
    t_mean = get_average_start_time(schedule_matrix)

    print("Max start time: {}".format(t_max))
    print("Average start time: {}".format(t_mean))

    

    scheduler_matrix_dict = {}

    scheduler_matrix_dict["Barcode"] = list(battery_obj_dict.keys())

    for i in range(max_weeks):
        scheduler_matrix_dict[f"Week_{i}"] = schedule_matrix[:,i]

    schedule_df = pd.DataFrame.from_dict(scheduler_matrix_dict)
    schedule_df = schedule_df.set_index("Barcode")

    return schedule_df


def batteries_to_test_week(schedule_df, week):
    """Will return the barcodes of batteries that are to be tested on a specific week"""

    week = 0 
    week_df = schedule_df[f"week_{week}"]
    barcode_to_test = list(week_df[week_df==1].index)

    return barcode_to_test