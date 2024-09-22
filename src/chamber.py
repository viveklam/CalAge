import pandas as pd
import json
from datetime import datetime


class TemperatureChamber:

    def __init__(self, name, temperature, battery_list=[], battery_under_diagnostic=[]):
        """
        Constructor of a Temperature Chamber object.

        Parameters
        ----------
        :param name: str
            Name of the temperature chamber that will help in finding it in the lab
        :param temperature: int
            Temperature that the temperature chamber is being held at
        :param battery_list: [str]
            List of all the batteries barcodes that belong in this temperature chamber. 
        :param battery_under_diagnostic: [str]
            List of all batteries barcodes that are currently being tested in a diagnostic chamber
            so although they are part of battery_list they will not be found in this chamber

        TODO: Could potentially augment this to say which rack etc a battery would be on to
                help find it. Or it could be ordered based on where it should be in the chamber.
        """
        self.name = str(name)
        self.battery_list = list(battery_list)
        self.temperature = int(temperature)
        self.battery_under_diagnostic = list(battery_under_diagnostic)

    def load_batteries(self, new_batteries):
        """
        This function will add new batteries to the existing list of battery barcodes

        Args:
        :param new_batteries: [str]

        Returns: None
        """
        self.battery_list = self.battery_list+new_batteries

    def assign_battery(self, battery_obj):
        """
        This function assigns a battery to this temperature chamber. In doing so it adds the battery
        barcode to the chamber's battery list and updates the battery object's storage location and 
        current location to this chamber
        
        Args:
        :param battery_obj: Battery
            Battery object that is now going to be assigned to this chamber
        
        Returns: None
        """

        #First check if battery obj temperature equals this chambers temperature
        if battery_obj.temperature != self.temperature:
            raise Exception("Battery object temperature and chamber temperature do not match")
        
        #Then check if this barcode already exists in the chamber
        if battery_obj.barcode in self.battery_list:
            raise Exception("Battery barcode already exists in this chamber")

        battery_obj.storage_location = self.name
        battery_obj.current_location = self.name
        self.battery_list.append(battery_obj.barcode)

        return None
    
    def return_battery(self, battery_obj):
        """This will return the battery to this by removing it from the battery under diagnostic column"""

        return None



def load_new_temperature_chambers(file_path):
    """
    Takes in the path to a csv file to open. Opens it and initializes new temperature chambers in the file. 

    Args:
    :param file_path: str
        Path to csv file with temperature chamber channels. Should have a chamber_name, and temperature column.
        
    Returns: {"name": TemperatureChamber} return a dictionary with keys that are the chamber name and a value 
                of a TemperatureChamber object.
    """

    temp_chamber_df = pd.read_csv(file_path)
    temp_chamber_dict = {}
    for _, row in temp_chamber_df.iterrows():
        chamber_name = row["chamber_name"]
        temperature = row["temperature"]
        temp_chamber_dict[chamber_name] = TemperatureChamber(chamber_name, temperature)

    return temp_chamber_dict

def load_existing_temp_chambers(file_path):
    """
    Takes in the path to the json file where the existing temperature chambers are currently stored.

    Args:
    :param file_path: str
        Path to json file with all current temperature chamber information is stored

    Returns: {"chamber_name": TemperatureChamber} dictionary with temperature chamber name as key and a 
                TemperatureChamber obj as the value.
    """

    # Open the JSON file
    with open(file_path, 'r') as infile:
        json_temp_chamb_dict = json.load(infile)

    #generate dictionary of battery objects
    temp_chamb_obj_dict = {}
    for key in json_temp_chamb_dict.keys():
        temp_chamb_obj = TemperatureChamber(**json_temp_chamb_dict[key])
        temp_chamb_obj_dict[key] = temp_chamb_obj
    
    return temp_chamb_obj_dict



class DiagnosticChamber:
    def __init__(self, name, channels, in_operation=False, diagnostic_start_time=""):
        """
        Constructor of a Temeprature Chamber object.

        Could potentially augment this to say which rack a battery will be on

        Parameters
        ----------
        :param name: str
            Name of the diagnostic chamber which will help you find it in the lab.
        :param channels: Dict
            This is a dictionary with three columns: channel, state, and form_factor. The channel is a custom channel number such as "1, 2, 3",
            or "C1, D2, D3" etc, but must be unique for this Diagnostic Chamber. The state is "unoccupied"(no cell loaded and no test running),
            "loaded" (cell on but not running), or "running"(test occuring). "form_factor" will state what type of battery can be cycled on this
            channel. "battery" will show the barcode of the loaded or running cell on that channel. Example:
            {"channel": ["C1", "C2", "C3"]
            "state": ["unoccupied", "loaded", "loaded"]
            "form_factor": ["21700", "pouch", "any"]}
            "battery": ["", "002345", "CAL002"]

        :param in_operation: Boolean
            Indicating whether the Diagnostic chamber is currently testing cells or not
        :param diagnostic_start_time: str
            This contains a datetime format of when the diagnostic was started. 
        """

        self.name = str(name)
        self.channels = channels
        self.in_operation = bool(in_operation)
        self.diagnostic_start_time = diagnostic_start_time
    
    def cell_compatible(self, channel_num, form_factor):
        """
        This function defines the channel compatibility. This can be modified to handle whichever channel compatibility you would like
        such as "18650" and "21700" cells working with any channel labeled cylindrical for example.


        Args:
        channel_num: int
            Corresponds to the list index of the channel number

        form_factor: string
            Form factor of the battery that is trying to go in to the channel provided

        Returns: Boolean True if cell is compatible, False if not

        TODO: Add a field for if a channel is broken potentially. 
        """

        #If channel can support any form_factor for example modular cell holders
        if self.channels["state"][channel_num]!="unoccupied":
            return False
        elif self.channels["form_factor"][channel_num]=="any":
            return True
        #If form factor is direct match
        elif self.channels["form_factor"][channel_num]==form_factor:
            return True
        #Insert any other compatibilities here
        else:
            return False
    
    def assign_channels(self, batteries_to_test):
        """
        TODO: change these comments to match what is actually being done

        Given a list of Batteries to test it will find corresponding channels and report a list of
        channels that should be occupied with cells and what channels will remain unoccupied. 

        This function assumes that the number of batteries with a given form factor will be less than
        the amount of channels this chamber has. Properly checking for this needs to be done outside of
        this function otherwise an error will be thrown. 

        Args:
        :param batteries_to_test: [Battery]
            List of batteries that need to be tested
        
        Returns:
        Dictionary with keys as channels and the values being the barcode


        TODO: Have batteries preferentially go to the channel they were previously tested on
        TODO: This currently doesn't do any "smart" assignment. i.e. if there is an "any" channel and a "pouch" channel 
        and you try to load in a pouch cell and an 18650 cell in that order, the pouch cell may be assigned to the any 
        channel and the 18650 would fail in finding a channel. Could update this to include like a priority list if this
        proves to be a desired behavior
        TODO: Potentially order batteries so that they are easier to load/find (such as alphabetical order assigned to increasing
        channel number)
        """

        #Records all the battery assignments
        assignment_dict = {}
        temporarily_blocked = []

        for battery in batteries_to_test:
            assigned = False
            number_of_channels = len(self.channels["channel"])

            #Loop over all channels and see if one is compatible then break if found
            for channel_num in range(number_of_channels):
                if self.cell_compatible(channel_num, battery.form_factor) & (channel_num not in temporarily_blocked):
                    temporarily_blocked.append(channel_num)
                    assignment_dict[self.channels["channel"][channel_num]] = battery.barcode
                    assigned=True
                    break

            #If this loops through all channels and can not be assigned then raise an exception. Cells it go to up till now
            #will have been assigned, so you can not just rerun it. Would need to clear it first. Not expected for this to trigger.
            if not assigned:
                raise Exception("Battery {}, was unable to be assigned with form factor {}. Check channels and cells".format(battery.barcode, battery.form_factor))

        
        return assignment_dict

    
    def create_channel_check_list(self, assignment_dict, battery_obj_dict, csv_location = "diagnostic_testing_verification.csv"):
        """
        This function creates a barcode channel verification csv file to check against to prevent human error.

        Args:
        @assignment_dict: dict
            Dictionary of the channel name as the key and the barcode of the cell as the value

        @csv_location: str
            Location to save the verification
        """

        verification_dict = {}

        verification_dict["Barcode"] = []
        verification_dict["Current_Location"] = []
        verification_dict["Testing_location"] = []
        verification_dict["Channel"] = []
        verification_dict["Scanned_Barcode"] = []


        for key in assignment_dict:
            barcode = assignment_dict[key]
            battery = battery_obj_dict[barcode]
            verification_dict["Barcode"].append(battery.barcode)
            verification_dict["Current_Location"].append(battery.current_location)
            verification_dict["Testing_location"].append(self.name)
            verification_dict["Channel"].append(key)
            verification_dict["Scanned_Barcode"].append("")

        
        df = pd.DataFrame.from_dict(verification_dict)
        df.to_csv(csv_location, index=False)

        return None

    def verify_and_load(self, csv_location, battery_obj_dict, temp_chamb_obj_dict):
        """
        This function will verify that all scanned barcodes match what should be on 
        the channel, and if so it will load the battery on to the corresponding channel

        TODO: Fill out the rest of this function
        
        
        """

        verification_df = pd.read_csv(csv_location)
        #check if any cells were incorrectly loaded if so stop here
        incorrect_scanned_df = verification_df[(verification_df["Barcode"]!=verification_df["Scanned_Barcode"])]
        if len(incorrect_scanned_df)!=0:
            incorrect_channels = list(incorrect_scanned_df["Channel"])
            raise Exception("Incorrect barcodes on Channels: {}".format(incorrect_channels))

        #if verified now for each channel load the battery on to the diagnostic chamber and update battery locations
        for idx in range(len(verification_df)):
            channel_row = verification_df.iloc[idx]
            channel = channel_row.Channel
            barcode = channel_row.Barcode

            #update channel information
            channel_idx = self.channels["channel"].index(channel)
            self.channels["state"][channel_idx] = "loaded"
            self.channels["battery"][channel_idx] = barcode

            battery_obj = battery_obj_dict[barcode]
            #Tell temperature chamber battery is in diagnostic
            temp_chamb_location = battery_obj.storage_location
            temp_chamb_obj_dict[temp_chamb_location].battery_under_diagnostic.append(barcode)
            #Update current location
            battery_obj.current_location = self.name
        return None
    
    def get_batch_start_file(self, battery_obj_dict, save_location="batch_start.csv", cycler_type = "Biologic"):
        """
        Get automatic batch start file.

        TODO: Fill out comments
        TODO: Implement for different cyclers like Maccor
        """

        batch_start_dict = {}
        batch_start_dict["Channel"] = []
        batch_start_dict["File Name"] = []
        batch_start_dict["Setting File Name"] = []
        for channel_idx in range(len(self.channels["channel"])):
            if self.channels["state"][channel_idx]=="loaded":
                barcode = self.channels["battery"][channel_idx]
                channel_name = self.channels["channel"][channel_idx]
                #Generate file names
                data_file_name = battery_obj_dict[barcode].generate_data_file()
                procedure_file_name = battery_obj_dict[barcode].generate_procedure_file()

                #Add to dict for storage
                batch_start_dict["Channel"].append(channel_name)
                batch_start_dict["File Name"].append(data_file_name)
                batch_start_dict["Setting File Name"].append(procedure_file_name)

        batch_start_df = pd.DataFrame.from_dict(batch_start_dict)
        batch_start_df.to_csv(save_location)
        print("Batch Start File Saved at {}".format(save_location))

        return None

    def start_channel_testing(self, battery_obj_dict):
        """
        This function will start all batteries that are in the "loaded" state on the diagnostic chamber. 
        If the chamber is already active, or if a battery is still undergoing a diagnostic cycle it will 
        throw an error.

        Args:
        @battery_obj_dict: Dict{barcode: Battery}
            battery barcode as the key and the corresponding Battery data object as the key

        Returns: None
        """


        today_date = datetime.today().strftime('%Y-%m-%d %H:%M')
        if self.in_operation:
            raise Exception("Diagnostic Chamber is currently in operation")

        #check if any battery is under a diagnostic
        for channel_idx in range(len(self.channels["channel"])):
            if self.channels["state"][channel_idx]=="loaded":
                battery_barcode = self.channels["battery"][channel_idx]
                battery_obj = battery_obj_dict[battery_barcode]
                #Battery already under diagnostic stop
                if battery_obj.under_diag:
                    channel_name =  self.channels["channel"][channel_idx]
                    raise Exception("Battery {} on Channel {} is already under Diagnostic".format(battery_barcode, channel_name))

        #If everything else is good start on the channels
        self.in_operation = True
        channels_started = []
        for channel_idx in range(len(self.channels["channel"])):

            self.diagnostic_start_time = today_date
            #if a channel is loaded, start it and update chamber channel info and battery info
            if self.channels["state"][channel_idx]=="loaded":
                
                battery_barcode = self.channels["battery"][channel_idx]
                battery_obj = battery_obj_dict[battery_barcode]

                #Change all battery attributes
                battery_obj.under_diag = True
                battery_obj.testing_start_dates.append(today_date)
                #Record files tested
                data_file_name = battery_obj.generate_data_file()
                battery_obj.test_file_in_progress = data_file_name
                battery_obj.data_file_history.append(data_file_name)
                procedure_file_name = battery_obj.generate_procedure_file()
                battery_obj.testing_procedure_history.append(procedure_file_name)

                #Change channel status
                self.channels["state"][channel_idx]="running"

                channels_started.append(self.channels["channel"][channel_idx])

        print("Channels started successfully: {}".format(channels_started))
        return None

    def diagnostic_finished(self, battery_obj_dict):
        """
        Confirm that the batteries are done testing. If done testing move everything that is running
        to a completed state and put chamber in idle state. Batteries diagnostic number will now be 
        incremented. Anything to be done at the previous diagnostic number should be done before this.

        Args:
        battery_obj_dict: Dict{barcode: Battery}
            battery barcode as the key and the corresponding Battery data object as the key

        Returns: None
        """

        if not self.in_operation:
            raise Exception("Diagnostic Chamber is not currently in operation")

        #If everything else is good start on the channels
        self.in_operation = False
        channels_reset = []
        for channel_idx in range(len(self.channels["channel"])):

            #if a channel is loaded, start it and update chamber channel info and battery info
            if self.channels["state"][channel_idx]=="running":
                
                battery_barcode = self.channels["battery"][channel_idx]
                battery_obj = battery_obj_dict[battery_barcode]

                #Change all battery attributes
                battery_obj.under_diag = False
                battery_obj.diagnostic_number+=1
                battery_obj.test_file_in_progress = ""

                #Change channel status
                self.channels["state"][channel_idx]="completed"

                channels_reset.append(self.channels["channel"][channel_idx])

        print("Channels reset successfully: {}".format(channels_reset))
        return None

    def generate_return_check_list(self, battery_obj_dict, csv_save_path = "chamber_return_verification.csv", 
                                        sort_by=["Storage_location", "Channel"]):
        """
        This function creates a barcode temperature chamber return verification csv file to check against to prevent human error.

        Args:
        battery_obj_dict: Dict{barcode: Battery}
            battery barcode as the key and the corresponding Battery data object as the key
        csv_location: str
            Location to save the verification
        sort_by: [str]
            This will simply sort the csv by the column chosen. Options are Barcode, Channel, Storage_location. If list is
            longer than one value it will first sort based on the first column then the second, and so on in ascending
            order. ex: ["Storage_location", "Channel"], will first sort by temperature chamber name, then by channel. 

        Returns: None
        """

        return_dict = {}

        return_dict["Barcode"] = []
        return_dict["Current_Location"] = []
        return_dict["Channel"] = []
        return_dict["Storage_Location"] = []
        return_dict["Scanned_Barcode"] = []

        for channel_idx in range(len(self.channels["channel"])):
            if self.channels["state"][channel_idx]=="completed":
                barcode = self.channels["battery"][channel_idx]
                battery = battery_obj_dict[barcode]
                return_dict["Barcode"].append(battery.barcode)
                return_dict["Current_Location"].append(battery.current_location)
                return_dict["Channel"].append(self.channels["channel"][channel_idx])
                return_dict["Storage_Location"].append(battery.storage_location)
                return_dict["Scanned_Barcode"].append("")

        df = pd.DataFrame.from_dict(return_dict)
        df.sort_values(sort_by, inplace=True)

        df.to_csv(csv_save_path, index=False)
        print("Return checklist generated at {}".format(csv_save_path))
        return None

    def verify_and_return(self, return_csv_path, battery_obj_dict, temp_chamb_obj_dict):
        """
        This function verifies that the scanned barcode matches the actual barcode for where the battery should 
        have gone back to. 

        Args:
        return_csv_path: str
            Path where the return verification csv path is saved
        battery_obj_dict: Dict{barcode: Battery}
            Dictionary of barcode as key and Battery as the value
        temp_chamb_obj_dict: Dict{chamber_name: TemperatureChamber}
            Dictionary of chamber name as key and TemperatureChamber object as the value
        
        Returns: None
        """

        verification_df = pd.read_csv(return_csv_path)
        #check if any cells were incorrectly returned if so stop here
        incorrect_scanned_df = verification_df[(verification_df["Barcode"]!=verification_df["Scanned_Barcode"])]
        if len(incorrect_scanned_df)!=0:
            incorrect_barcode = list(incorrect_scanned_df["Barcode"])
            raise Exception("Incorrect barcodes returned: {}".format(incorrect_barcode))
        
        #if verified, now return batteries to their storage location, and reset diagnostic chamber
        for idx in range(len(verification_df)):
            channel_row = verification_df.iloc[idx]
            channel = channel_row.Channel
            barcode = channel_row.Barcode

            #update channel information
            channel_idx = self.channels["channel"].index(channel)
            self.channels["state"][channel_idx] = "unoccupied"
            self.channels["battery"][channel_idx] = ""

            battery_obj = battery_obj_dict[barcode]
            temp_chamb_obj = temp_chamb_obj_dict[battery_obj.storage_location]
            #Tell temperature chamber battery is no longer in diagnostic
            temp_chamb_obj.battery_under_diagnostic.remove(barcode)
            #Update current location
            battery_obj.current_location = temp_chamb_obj.name
        
        print("All batteries returned successfully")
        return None


def load_new_diagnostic_chambers(file_path):
    """
    Takes in the path to a csv file to open. Opens it and initializes new diagnostic chambers in the file. 

    Args:
    :param file_path: str
        Path to csv file with DiagnosticChamber channels. Should have a chamber_name, channel and form_factor
        column. All channels will start unoccupied. 
        
    Returns: {"name": DiagnosticChamber} return a dictionary with keys that are the chamber name and a value 
                of a DiagnosticChamber object.
    """

    #Using pandas to load in csv more cleanly
    channel_df = pd.read_csv(file_path)
    unique_diag_chambers = set(channel_df["chamber_name"])
    diag_chamber_dict = {}

    for diag_chamber_name in unique_diag_chambers:
        diag_chamber_channel_df = channel_df[channel_df["chamber_name"]==diag_chamber_name][["channel", "form_factor"]]
        channel_dict = diag_chamber_channel_df.to_dict(orient="list")
        #set all channels to unoccupied
        channel_dict["state"] = ["unoccupied"]*len(channel_dict["channel"])
        #Set all batteries to an empty string since the channels are unoccupied
        channel_dict["battery"] = [""]*len(channel_dict["channel"])
        #initialize diagnostic chamber
        diag_chamber = DiagnosticChamber(name=diag_chamber_name, channels=channel_dict)
        diag_chamber_dict[diag_chamber.name] = diag_chamber

    return diag_chamber_dict

def load_existing_diag_chambers(file_path):
    """
    Takes in the path to the json file where the existing diagnostic chambers are currently stored.

    Args:
    :param file_path: str
        Path to json file with all current diagnostic chamber state and information stored

    Returns: {"chamber_name": DiagnosticChamber} dictionary with diagnostic chamber name as key and a 
                DiagnosticChamber obj as the value.
    """

    # Open the JSON file
    with open(file_path, 'r') as infile:
        json_diag_chamb_dict = json.load(infile)

    #generate dictionary of battery objects
    diag_chamb_obj_dict = {}
    for key in json_diag_chamb_dict.keys():
        diag_chamb_obj = DiagnosticChamber(**json_diag_chamb_dict[key])
        diag_chamb_obj_dict[key] = diag_chamb_obj

    return diag_chamb_obj_dict