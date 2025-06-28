# script to display and save data from global alianment PSD through serial port 
#
# revision 0.1, 09/30/2024, Weidong Jin UCLA

import tkinter as tk
from tkinter import filedialog, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
import threading
import faulthandler
import serial

faulthandler.enable()


# Dummy data generator (Replace with actual serial communication)
def get_serial_data(ser):
     data = ser.readline().decode().strip()  # Read and decode data 
#     data=ser.read(1000)
#     print (data)
     return data

# Main Application class
class SerialPlotApp:
    def __init__(self, root):
        self.running = False  # Flag to control the receiving loop
        self.root = root
        self.root.title("Serial Data Plotter V1.0 Weidong")

        # Set up the figure for plotting cross markers
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.axhline(0, color='black', lw=1)  # Horizontal line
        self.ax.axvline(0, color='black', lw=1)  # Vertical line
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        # Plot initial cross markers without labels
        self.cross_marker1, = self.ax.plot([0], [0], marker="x", color="blue",label="PSD1")
        self.cross_marker2, = self.ax.plot([0], [0], marker="x", color="red",label="PSD2")

        # Annotate the markers with labels PSD1 and PSD2
        self.label1 = self.ax.annotate("PSD1", xy=(0, 0), xytext=(-5,-5),
                                       textcoords="offset points", color="blue")
        self.label2 = self.ax.annotate("PSD2", xy=(0, 0), xytext=(5, 5),
                                       textcoords="offset points", color="red")

       
         # Add legend to the plot
        self.ax.legend(loc='upper right')  # Add legend and set its location
        # Create GUI layout
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.data_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=50, height=10)
        self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Save Button
        self.save_button = tk.Button(self.root, text="Save Data", command=self.save_data)
        self.save_button.pack(side=tk.LEFT)

        # Start Button
        self.start_button = tk.Button(self.root, text="Start", command=self.start_receiving_data)
        self.start_button.pack(side=tk.RIGHT)
       # Stop Button
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_receiving_data)
        self.stop_button.pack(side=tk.RIGHT)
        # Data storage
        self.data_list = []


    def stop_receiving_data(self):
        self.running = False  # Stop the data-receiving loop

    # Function to start receiving data
    def start_receiving_data(self):
        self.running = True  # Set the flag to True when starting
        threading.Thread(target=self.receive_data, daemon=True).start()

    # Function to simulate receiving serial data
    def receive_data(self):
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        while self.running:
            data = get_serial_data(ser)  # Replace with actual serial reading
            self.parse_and_update(data)

    # Function to parse serial data and update the GUI
    def parse_and_update(self, data):
        # Parse the incoming data
        parsed_data = self.parse_serial_data(data)
        
        if (parsed_data!=None): 
            # Update the cross markers
            self.update_cross_markers(parsed_data)

        # Append data with a timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        full_data = f"{timestamp} - {data}\n"
        self.data_display.insert(tk.END, full_data)
        self.data_display.see(tk.END)
        
        # Store the data
        self.data_list.append(full_data)

    # Function to parse the incoming serial data string
    def parse_serial_data(self, data):
        # Check if the line is a comment and skip it
        if data.startswith('#'):
             return None
    
        try:
             # Split the line into individual float values
             values = list(map(float, data.split()))
        
             # Ensure we have at least 4 values (x1, y1, x2, y2)
             if len(values) >= 4:
                 parsed_data = {
                     'x1': values[0],
                     'y1': values[1],
                     'x2': values[2],
                     'y2': values[3] 
                 }
                 return parsed_data
             else:
                # If the line doesn't contain enough values, return None
                 return None
        except ValueError:
             # If conversion to float fails, ignore the line
            return None              

    # Function to update the cross markers based on parsed data
    def update_cross_markers(self, data):
        x1, y1 = data.get('x1', 0), data.get('y1', 0)
        x2, y2 = data.get('x2', 0), data.get('y2', 0)

        # Update marker positions
        self.cross_marker1.set_data([x1], [y1])
        self.cross_marker2.set_data([x2], [y2])

        # Update label positions to follow markers
        self.label1.set_position((x1, y1))
        self.label2.set_position((x2, y2))

        # Redraw plot
        self.canvas.draw()

    # Function to save the data to a file
    def save_data(self):
        file_name = filedialog.asksaveasfilename(defaultextension=".txt", 
                                                 filetypes=[("Text files", "*.txt")])
        if file_name:
            with open(file_name, 'w') as f:
                f.writelines(self.data_list)

# Main function to run the app
def main():
    root = tk.Tk()
    app = SerialPlotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
