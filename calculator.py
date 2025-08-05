from ttkbootstrap import TtkBootstrap
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import ttk

# Initialize the TtkBootstrap GUI
tk = TtkBootstrap()

# Define the UI layout
def calculator_ui():
    # Create a window
    win = ttk.Tk()
    win.title("Calculator")
    win.geometry("300x400")

    # Add a frame for the display
    display_frame = ttk.Frame(win)
    display_frame.grid(column=0, row=0, columnspan=4, padx=10, pady=10)

    # Add a display label
    display_label = ttk.Label(display_frame, text="0", font=("Arial", 24), foreground="white", background="black")
    display_label.grid(column=0, row=0, columnspan=4, padx=10, pady=10)

    # Define the calculation variables
    display_value = "0"
    calculation = ""
    decimal_used = False

    # Function to handle button clicks
    def button_click(value):
        global display_value, calculation, decimal_used
        if value == "C":
            display_value = "0"
            calculation = ""
        elif value == "+/-":
            if display_value[0] == "-":
                display_value = display_value[1:]
            else:
                display_value = "-" + display_value
        elif value == "CE":
            display_value = "0"
            calculation = ""
        elif value == "=":
            try:
                result = eval(calculation)
                display_value = str(result)
            except:
                display_value = "ERROR"
        elif value == "Back":
            display_value = display_value[:-1]
        else:
            if value == ".":
                if not decimal_used:
                    decimal_used = True
            display_value += value
            if value.isdigit() or value == ".":
                calculation += value

    # Create a function to update the display
    def update_display():
        display_label.config(text=display_value)

    # Create the button grid
    for i in range(1, 10):
        button = ttk.Button(win, text=str(i), command=lambda x=i: button_click(x))
        button.grid(column=i % 4 + 1, row=i // 4 + 1, padx=10, pady=10)

    # Add other buttons
    zero_button = ttk.Button(win, text="0", command=lambda x="0": button_click(x))
    zero_button.grid(column=1, row=4, padx=10, pady=10)

    decimal_button = ttk.Button(win, text=".", command=lambda x="0.": button_click(x))
    decimal_button.grid(column=2, row=4, padx=10, pady=10)

    plus_minus_button = ttk.Button(win, text="+/-", command=lambda: button_click("+/-"))
    plus_minus_button.grid(column=3, row=4, padx=10, pady=10)

    clear_button = ttk.Button(win, text="C", command=lambda: button_click("C"))
    clear_button.grid(column=0, row=4, padx=10, pady=10)

    clear_entry_button = ttk.Button(win, text="CE", command=lambda: button_click("CE"))
    clear_entry_button.grid(column=0, row=5, padx=10, pady=10)

    back_button = ttk.Button(win, text="Back", command=lambda: button_click("Back"))
    back_button.grid(column=1, row=5, padx=10, pady=10)

    equals_button = ttk.Button(win, text="=", command=lambda: button_click("="), width=2)
    equals_button.grid(column=2, row=5, padx=10, pady=10)