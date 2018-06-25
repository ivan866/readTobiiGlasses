from data.XMLSettings import XMLSettings





class Corpora:
    """Multichannel data collection. Main data structure class.

    """

    def __init__(self):
        """

        """
        self.settings = XMLSettings()



    def select_settings(self, file:str=None) -> None:
        """

        :return:
        """
        #callback function to set status textfield in main window
        self.settings.status_cb=self.status_cb
        self.settings.error_cb=self.error_cb
        self.settings.select(file)








#validation
#if len(self.getIntervals(ignoreEmpty=True)) == 0:
#   self.status_cb('WARNING: No intervals specified. Please explicitly specify at least 1 named interval in settings file.')