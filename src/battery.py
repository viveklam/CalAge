from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import datetime


class Battery:

    def __init__(self, proj_name, barcode, seqnum, temperature, soc, diagnostic_frequency, 
                form_factor, next_diag="today", storage_location="Unassigned", current_location="Unassigned",
                testing_files = [], testing_start_dates=[], test_file_in_progress="", active_status=True, under_diag=False,
                diagnostic_number=0, setting_file_proj_name=None):
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
        :param diagnostic_frequency: int
            The frequency of diagnostic of the battery in days.
        :param form_factor: string
            The formfactor of the battery. Should be 
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
        self.form_factor = str(form_factor)

        self.active_status = bool(active_status)
        self.under_diag = bool(under_diag)
        self.diagnostic_number = int(diagnostic_number)

        self.storage_location = str(storage_location)
        self.current_location = str(current_location)

        #Storing the history of the files and diagnostic run
        self.testing_files = list(testing_files)
        self.testing_start_dates = list(testing_start_dates)
        self.test_file_in_progress = str(test_file_in_progress)
        
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
            
    def ready_for_checkup(self):
        """
        This method is used to determine whether it is time for the battery to
        go through a diagnostic or a checkup cycle.

        Returns: True if today is later than the next diagnostic. False if not
        """

        next_diag_datetime = datetime.strptime(self.next_diag, "%m/%d/%Y")
        return date.today() >= next_diag_datetime
        
    def generateDataFile(self):
        """
        Returns a file name to store the data in.
        """
        return "{}_{}_{}_CU{}".format(self.proj_name, self.seqnum, self.barcode, self.diagnostic_number)

    def generateSettingFile(self):
        #NEED TO UPDATE THIS FUNCTION
        #To properly do this I think I need to add a setting file name
        return "{}_{}SOC.mps".format(self.proj_name, self.soc)