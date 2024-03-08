class TemperatureChamber:

    def __init__(self, name, battery_list, temperature):
        """
        Constructor of a Temperature Chamber object.

        Parameters
        ----------
        :param name: str
            Name of the temperature chamber that will help in finding it in the lab
        :param battery_list: [str]
            List of all the batteries barcodes that belong in this temperature chamber. 
        :param temperature: int
            Temperature that the temperature chamber is being held at

        TODO: Could potentially augment this to say which rack a battery will be on
        """
        self.name = str(name)
        self.battery_list = list(battery_list)
        self.temperature = int(temperature)

    def load_batteries(self, new_batteries):
        """
        This function will add new batteries to the existing list of battery barcodes

        Args:
        :param new_batteries: [str]

        Returns: None
        """
        self.battery_list = self.battery_list+new_batteries


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
    
    def load_batteries(self, batteries_to_test):
        """
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

        for battery in batteries_to_test:
            assigned = False
            number_of_channels = len(self.channels["channel"])

            #Loop over all channels and see if one is compatible then break if found
            for channel_num in range(number_of_channels):
                if self.cell_compatible(channel_num, battery.form_factor):
                    #Assign this cell to this channel
                    self.channels["state"][channel_num]="loaded"
                    self.channels["battery"][channel_num]=battery.barcode
                    #Change battery's current location to this diagnostic chamber
                    battery.current_location = self.name

                    assignment_dict[self.channels["channel"][channel_num]] = battery.barcode
                    assigned=True
                    break

            #If this loops through all channels and can not be assigned then raise an exception. Cells it go to up till now
            #will have been assigned, so you can not just rerun it. Would need to clear it first. Not expected for this to trigger.
            if not assigned:
                raise Exception("Battery {}, was unable to be assigned with form factor {}. Check channels and cells".format(battery.barcode, battery.form_factor))

        
        return assignment_dict


    def estimated_end_time(self, assignment_dict):
        """This function will return the estimate for when."""
        pass


        
    def generate_automatic_testing_file():
        """ """
        pass


    def start_testing(self):
        """
        Switches the diagnostic chamber to be actively testing.
        """
        self.in_operation = True

        pass

