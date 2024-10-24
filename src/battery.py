from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json
import csv
import re


class Battery:

    def __init__(self, proj_name, barcode, seqnum, temperature, soc, diagnostic_frequency, cell_type,
                form_factor, next_diag="today", storage_location="Unassigned", current_location="Unassigned",
                data_file_history = [], testing_procedure_history = [], testing_start_dates=[], test_file_in_progress="", active_status=True, under_diag=False,
                data_file_template = "{battery.proj_name}_{battery.barcode}_{battery.seqnum}_CU{battery.diagnostic_number}", 
                procedure_file_template = "{battery.proj_name}_{battery.cell_type}_{battery.soc}SOC.mps", diagnostic_number=0):
        """
        Constructor of a Battery object.

        Parameters
        ----------
        :param proj_name: str
            The Project name of the battery
        :param barcode: str
            The barcode of the battery.
        :param seqnum: str
            The sequence number of the battery.
        :param temperature: int
            The temperature of the battery.
        :param cell_type: str
            The cell type i.e. K2EnergyLFPE, etc. Something that uniquely idenfitifies cells of 
            a group together.
        :param diagnostic_frequency: int
            The frequency of diagnostic of the battery in days.
        :param form_factor: string
            The formfactor of the battery. Should be ["21700", "18650", "pouch", "prismatic"]
        :param soc: int
            The state of charge of the battery.
        :param next_diag: string
            When the next diagnostic should occur. Either today, or give a date in MM/DD/YYYY format.
            i.e. 01/29/2024.
        """

        self.proj_name = str(proj_name)
        self.barcode = str(barcode)
        self.seqnum = str(seqnum)
        self.temperature = int(temperature)
        self.soc = int(soc)
        self.diagnostic_frequency = int(diagnostic_frequency)
        self.cell_type = cell_type
        self.form_factor = str(form_factor)

        self.active_status = bool(active_status)
        self.under_diag = bool(under_diag)
        self.diagnostic_number = int(diagnostic_number)

        self.storage_location = str(storage_location)
        self.current_location = str(current_location)

        #Storing the history of the files and diagnostic run
        self.data_file_history = list(data_file_history)
        self.testing_procedure_history = list(testing_procedure_history)
        self.testing_start_dates = list(testing_start_dates)
        self.test_file_in_progress = str(test_file_in_progress)

        #Naming convention
        self.data_file_template = data_file_template
        self.procedure_file_template = procedure_file_template
        
        #Get next diagnostic
        if next_diag != "today":
            today_date = date.today()
            self.next_diag = today_date.strftime("%m/%d/%Y")
        else:
            self.next_diag = next_diag

        #check if valid form factor
        valid_form_factors = ["21700", "18650", "pouch", "prismatic"]
        if form_factor not in valid_form_factors:
            raise ValueError("Choose valid form factor from: {}".format(valid_form_factors))
            
    def ready_for_checkup(self, template):
        """
        This method is used to determine whether it is time for the battery to
        go through a diagnostic or a checkup cycle.
        Args:
        template: str
            String 

        Returns(Boolean): True if today is later than the next diagnostic. False if not
        """

        next_diag_datetime = datetime.strptime(self.next_diag, "%m/%d/%Y")
        return date.today() >= next_diag_datetime
        
    def generate_data_file(self):
        """
        Generates a filename from the battery data object. Can be whatever user wants from the attributes of the 
        battery data object. If using an attribute specifify in format {battery.field}.

        TODO: Add functionality for a repeat test if an error has occure i.e. _v1 or something

        Returns: filename string
        """

        template = self.data_file_template

        try:
            # Find all placeholders in the format "battery.<field>"
            placeholders = re.findall(r"\{battery\.(\w+)\}", template)

            # For each placeholder, get the attribute from the battery object and replace it in the template
            for placeholder in placeholders:
                value = getattr(self, placeholder, None)
                if value is None:
                    raise ValueError(f"Invalid field '{placeholder}' for battery object")
                # Replace the placeholder with the actual value
                template = template.replace(f"{{battery.{placeholder}}}", str(value))

            return template
        except AttributeError as e:
            raise ValueError(f"Error in template: {e}")


    def generate_procedure_file(self, template = "{battery.proj_name}_{battery.cell_type}_{battery.soc}SOC.mps"):
        """
        Generates a procedure file from the battery data object. The procedure file is the testing file that 
        is used to test the battery such as what is used by the Biologic or Maccor. The procedure file should
        already be on the computer before the test, and is typically used repeatedly.

        Returns: filename string
        """

        template = self.procedure_file_template

        try:
            # Find all placeholders in the format "battery.<field>"
            placeholders = re.findall(r"\{battery\.(\w+)\}", template)

            # For each placeholder, get the attribute from the battery object and replace it in the template
            for placeholder in placeholders:
                value = getattr(self, placeholder, None)
                if value is None:
                    raise ValueError(f"Invalid field '{placeholder}' for battery object")
                # Replace the placeholder with the actual value
                template = template.replace(f"{{battery.{placeholder}}}", str(value))

            return template
        except AttributeError as e:
            raise ValueError(f"Error in template: {e}")

    def generateSettingFile(self):
        """
        Generates a setting file based on the function provided below. 
        Update this function if you want the filename to be different.
        """
        return "{}_{}_{}SOC.mps".format(self.proj_name, self.cell_type, self.soc)


def load_new_batteries(file_path):
    """
    Takes in the path to a csv file to open. Opens it and initializes new batteries to start.

    Args:
    :param file_path: str
        Path to csv file with battery to initalize. Needs at least the columns in the header:
        proj_name, barcode, seqnum, temperature, soc, diagnostic_frequency, form_factor.
    
    Returns: {"barcode": Battery} dictionary with battery barcode as key and a Battery obj as the
                value.
    """

    #Open csv and get a list of the dictionaries key is header
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        battery_init_dicts = [row for row in csv_reader]

    # For each of the rows in the csv, pass it all in to the battery object and make a battery object 
    # and store in list
    battery_obj_dict = {}
    for battery_dict in battery_init_dicts:
        battery_obj = Battery(**battery_dict)
        battery_obj_dict[battery_obj.barcode] = battery_obj
    
    return battery_obj_dict

def load_existing_batteries(file_path):
    """
    Takes in the path to the json file where the existing batteries are currently stored.

    Args:
    :param file_path: str
        Path to json file with all current batteries stored

    Returns: {"barcode": Battery} dictionary with battery barcode as key and a Battery obj as the
                value.
    """

    # Open the JSON file
    with open(file_path, 'r') as infile:
        json_battery_dict = json.load(infile)

    #generate dictionary of battery objects
    battery_obj_dict = {}
    for key in json_battery_dict.keys():
        battery_obj = Battery(**json_battery_dict[key])
        battery_obj_dict[key] = battery_obj

    return battery_obj_dict


    