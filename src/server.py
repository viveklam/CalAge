import csv
import json

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


