import csv
import json

def load_new_batteries(file_path):
    """
    Takes in the path to a csv file to open. Opens it and initializes new batteries to start.

    Args:
    :param file_path: str
        Path to csv file with battery to initalize. Needs at least the columns in the header:
        proj_name, barcode, seqnum, temperature, soc, diagnostic_frequency, form_factor.
    
    Returns: [Battery] List of battery objects
    """

    #Open csv and get a list of the dictionaries key is header
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        battery_init_dicts = [row for row in csv_reader]

    # For each of the rows in the csv, pass it all in to the battery object and make a battery object 
    # and store in list
    battery_list = []
    for battery_dict in battery_init_dicts:
        battery_obj = Battery(**battery_dict)
        battery_list.append(battery_obj)
    
    return battery_list



def save_battery_to_json(battery_list, file_path):
    """
    This function will save the battery list to the json file that is specified. The json file structure will be
    a large dict with keys equal to the barcode of the battery and the value is a dictionary which is a battery objects
    dictionary. i.e. {"0000A": {barcode:"0000A", under_diag: False, etc}, "0000B": etc}.

    Args:
    :param battery_list: [Battery]
        This is a list of Battery data objects. It should have all the battery data objects that need to be used
    :param: file_path: str
        This is a filepath to the json file that should be saved. If there is anything else here it will be overwritten
    
    Returns: None
    """

    #Convert battery_list to a dictonary representation
    json_battery_dict = {}
    for battery in battery_list:
        key = battery.barcode
        json_battery_dict[key] = battery.__dict__

    #write in to the json file
    with open(file_path, 'w') as f:
        json.dump(json_battery_dict, f)

