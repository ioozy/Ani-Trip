import customtkinter as ctk
from gui_app import AnitabiApp

ctk.set_widget_scaling(1.0)  
ctk.set_window_scaling(1.0)

def main():
    app = AnitabiApp()
    app.mainloop()

if __name__ == "__main__":
    main()