from simple_to_pdf.app_dialog import InfoDialog
from simple_to_pdf.localization.localization_mixin import LocalizationMixin


class NotificationManager(LocalizationMixin):
    def __init__(self, master):
        self.master = master

    def show_msg(
        self,
        scenario_key: str = "info",
        **kwargs,
    ):

        InfoDialog(parent=self.master, scenario_key=scenario_key, **kwargs)
    
    def show_status(self):
        pass
    
