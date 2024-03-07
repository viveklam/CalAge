class TemperatureChamber:

    def __init__(self, name, battery_list, temperature):
        """
        Constructor of a Temeprature Chamber object.

        Could potentially augment this to say which rack a battery will be on

        Parameters
        ----------
        :param name: str
            Name of the temperature chamber that will help in finding it in the lab
        :param battery_list: [str]
            List of all the batteries barcodes that belong in this temperature chamber. 
        :param temperature: int
            Temperature that the temperature chamber is being held at
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
