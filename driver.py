#-----------------------------------------------------
#Driver Script to integrate entire execution via a GUI
#Currently in progress!
#-----------------------------------------------------  

from email.mime import image
import tkinter
import tkinter.messagebox
import customtkinter
from PIL import Image, ImageTk
import os

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATH = os.path.dirname(os.path.realpath(__file__))
class App(customtkinter.CTk):

    WIDTH = 900
    HEIGHT = 520

    def __init__(self):
        super().__init__()

        self.title("Stock Screener")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        self.bell_image = self.load_image("Prerequisites-Outputs\LOGOn.PNG",130,70)

        # ============ create two frames ============

        # configure grid layout (2x1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=80,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

        self.frame_new=customtkinter.CTkFrame(master=self,
                                                 width=140,
                                                 height=50,
                                                 corner_radius=0)
        self.frame_new.grid(row=0, column=2, sticky="nswe", padx=20, pady=20)

       
       

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_rowconfigure(0, minsize=10)   # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(7, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)    # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        self.label_1 = customtkinter.CTkLabel(master=self.frame_left,
                                              image=self.bell_image,
                                              text_font=("Roboto Medium", -18))  # font name and size in px
        self.label_1.grid(row=1, column=0, pady=10, padx=10)

       

        self.label_mode = customtkinter.CTkLabel(master=self.frame_left, text="Appearance Mode:")
        self.label_mode.grid(row=9, column=0, pady=0, padx=20, sticky="w")

        self.optionmenu_1 = customtkinter.CTkOptionMenu(master=self.frame_left,
                                                        values=["Light", "Dark", "System"],
                                                        command=self.change_appearance_mode,fg_color="#3d86a8")
        self.optionmenu_1.grid(row=10, column=0, pady=10, padx=20, sticky="w")

        # ============ frame_right ============

        # configure grid layout (3x7)
        self.frame_right.rowconfigure((0, 1, 2, 3), weight=1)
        self.frame_right.rowconfigure(7, weight=10)
        self.frame_right.columnconfigure((0, 1), weight=1)
        self.frame_right.columnconfigure(2, weight=0)


        # ============ frame_info ============

        # configure grid layout (1x1)
        self.frame_info = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)
        self.frame_info.grid(row=0, column=0, columnspan=6, rowspan=8, pady=15, padx=15, sticky="nsew")


        self.label_info_1 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Ticker Screeners" ,
                                                   height=40,
                                                   corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "#3d86a8"),  # <- custom tuple-color
                                                   justify=tkinter.LEFT)
        self.label_info_1.grid(column=0, row=0, sticky="nwe", padx=15, pady=15)
        self.label_info_1.place(relx=0.5, rely=0.1, anchor=tkinter.CENTER)

        
    
        self.radio_var = tkinter.IntVar(value=0)

        """self.label_radio_group = customtkinter.CTkLabel(master=self.frame_info)
        self.label_radio_group.grid(row=0, column=0, columnspan=1, pady=20, padx=10, sticky="")

        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.frame_info,
                                                           variable=self.radio_var,
                                                           value=0)
        self.radio_button_1.grid(row=1, column=0, pady=10, padx=20, sticky="n")

        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.frame_info,
                                                           variable=self.radio_var,
                                                           value=1)
        self.radio_button_2.grid(row=2, column=0, pady=10, padx=20, sticky="n")

        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.frame_info,
                                                           variable=self.radio_var,
                                                           value=2)
        self.radio_button_3.grid(row=3, column=0, pady=10, padx=20, sticky="n")

        self.check_box_1 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Attractive EV/EBITDA Ratio")
        self.check_box_1.grid(row=5, column=1, pady=10, padx=20, sticky="w")

        self.check_box_2 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Stocks below Book Value")
        self.check_box_2.grid(row=6, column=1, pady=10, padx=20, sticky="w")

        self.check_box_3 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Attractive P/S Ratio")
        self.check_box_3.grid(row=7, column=1, pady=10, padx=20, sticky="w")

        self.check_box_4 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Bullish Engulfing")
        self.check_box_4.grid(row=5, column=2, pady=10, padx=20, sticky="w")

        self.check_box_5 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Bearish Engulfing")
        self.check_box_5.grid(row=6, column=2, pady=10, padx=20, sticky="w")
        
        self.check_box_6 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Gravestone Doji")
        self.check_box_6.grid(row=7, column=2, pady=10, padx=20, sticky="w")
        
        
        self.check_box_7 = customtkinter.CTkCheckBox(master=self.frame_screen,
                                                     text="Attractive P/S and P/BV")
        self.check_box_7.grid(row=8, column=1, pady=10, padx=20, sticky="w")"""

        self.label_info_2 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Attractive EV/EBITDA Ratio" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_2.grid(column=0, row=1, sticky="nwe", padx=15, pady=15)
        self.label_info_2.place(relx=0.05,rely=0.3)


        self.label_info_3 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Stocks below Book Value" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_3.grid(column=0, row=2, sticky="nwe", padx=15, pady=15)
        self.label_info_3.place(relx=0.05,rely=0.4)


        self.label_info_4 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Attractive Price/Sales Ratio" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_4.grid(column=0, row=3, sticky="nwe", padx=15, pady=15)
        self.label_info_4.place(relx=0.05,rely=0.5)


        self.label_info_5 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Bullish Engulfing Pattern" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_5.grid(column=0, row=4, sticky="nwe", padx=15, pady=15)
        self.label_info_5.place(relx=0.05,rely=0.6)


        self.label_info_6 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Bearish Engulfing Pattern" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_6.grid(column=0, row=5, sticky="nwe", padx=15, pady=15)
        self.label_info_6.place(relx=0.05,rely=0.7)


        self.label_info_7 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Gravestone Doji Pattern " ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_7.grid(column=0, row=6, sticky="nwe", padx=15, pady=15)
        self.label_info_7.place(relx=0.05,rely=0.8)


        self.label_info_8 = customtkinter.CTkLabel(master=self.frame_info,
                                                   text="Attractive P/S and P/BV" ,corner_radius=6,  # <- custom corner radius
                                                   fg_color=("white", "gray38"),width=60,justify=tkinter.CENTER)
                                                   
        self.label_info_8.grid(column=0, row=7, sticky="nwe", padx=15, pady=15)
        self.label_info_8.place(relx=0.05,rely=0.9)

        self.button_10 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_10.grid(row=2, column=1, pady=10, padx=20)
        self.button_10.place(relx=0.6,rely=0.3)


        self.button_11 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_11.grid(row=3, column=1, pady=10, padx=20)
        self.button_11.place(relx=0.6,rely=0.4)


        self.button_12 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_12.grid(row=4, column=1, pady=10, padx=20)
        self.button_12.place(relx=0.6,rely=0.5)

        self.button_13 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_13.grid(row=5, column=1, pady=10, padx=20)
        self.button_13.place(relx=0.6,rely=0.6)

        self.button_14 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")

        self.button_14.grid(row=6, column=1, pady=10, padx=20)
        self.button_14.place(relx=0.6,rely=0.7)

        self.button_15 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")

        self.button_15.grid(row=7, column=1, pady=10, padx=20)
        self.button_15.place(relx=0.6,rely=0.8)

        self.button_16 = customtkinter.CTkButton(master=self.frame_info,
                                                text="Fetch Now",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_16.grid(row=8, column=1, pady=10, padx=20)
        self.button_16.place(relx=0.6,rely=0.9)


        # ============ frame_right ============
      
        """self.combobox_1 = customtkinter.CTkComboBox(master=self.frame_right,
                                                    values=["Value 1", "Value 2"])
        self.combobox_1.grid(row=6, column=2, columnspan=1, pady=10, padx=20, sticky="we")"""

       
        self.entry = customtkinter.CTkEntry(master=self.frame_right,
                                            width=120,
                                            placeholder_text="Enter Ticker")
        self.entry.grid(row=8, column=0, columnspan=2, pady=20, padx=20, sticky="we")

        self.button_7 = customtkinter.CTkButton(master=self.frame_right,
                                                text="Fetch Valuation",
                                                border_width=2,  # <- custom border_width
                                                fg_color="#3d86a8",  # <- no fg_color
                                                command=self.button_event)
        self.button_7.grid(row=8, column=2, columnspan=1, pady=20, padx=20, sticky="we")


        # ============ frame_new ============

        # configure grid layout (1x1)
        self.frame_new.grid_rowconfigure(0, minsize=10)   # empty row with minsize as spacing
        self.frame_new.grid_rowconfigure(7, weight=1)  # empty row as spacing
        self.frame_new.grid_rowconfigure(8, minsize=20)    # empty row with minsize as spacing
        self.frame_new.grid_rowconfigure(11, minsize=10)  
        
        self.button_1 = customtkinter.CTkButton(master=self.frame_new,
                                                text="CSV Generator",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_1.grid(row=1, column=0, pady=10, padx=20)

        self.button_3 = customtkinter.CTkButton(master=self.frame_new,
                                                text="Financials Generator",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_3.grid(row=2, column=0, pady=10, padx=20)

        self.button_8 = customtkinter.CTkButton(master=self.frame_new,
                                                text="Mailer",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_8.grid(row=3, column=0, pady=10, padx=20)

        self.button_9 = customtkinter.CTkButton(master=self.frame_new,
                                                text="Available Tickers",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_9.grid(row=8, column=0, pady=10, padx=20)

        self.button_2 = customtkinter.CTkButton(master=self.frame_new,
                                                text="Garbage Collector",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_2.grid(row=9, column=0, pady=10, padx=20)

       

        self.button_6 = customtkinter.CTkButton(master=self.frame_new,
                                                text="Financial Garbage Collector",
                                                command=self.button_event,fg_color="#3d86a8")
        self.button_6.grid(row=10, column=0, pady=10, padx=20)

    
        # set default values
        self.optionmenu_1.set("Dark")
        #self.combobox_1.set("CTkCombobox")
        #self.check_box_1.configure(state=tkinter.DISABLED, text="CheckBox disabled")
        #self.check_box_2.select()

    def button_event(self):
        print("Button pressed")

    def load_image(self, path, width,height):
        return ImageTk.PhotoImage(Image.open(path).resize((width,height)))


    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def on_closing(self, event=0):
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
