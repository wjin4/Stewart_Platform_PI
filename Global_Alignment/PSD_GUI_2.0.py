import tkinter as tk
from tkinter import filedialog, scrolledtext, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time
import threading
import faulthandler
import serial
from collections import deque
import os.path

faulthandler.enable()

# Dummy data generator (Replace with actual serial communication)
def get_serial_data(ser):
    data = ser.readline().decode().strip()  # Read and decode data
    return data

# Main Application class
class SerialPlotApp:
    def __init__(self, root):
        self.running = False  # Flag to control the receiving loop
        self.root = root
        self.root.title("Serial Data Plotter V2.0 Weidong")

        # Set up the figure for plotting cross markers
        self.fig, self.ax = plt.subplots(figsize=(2, 2))
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.axhline(0, color='black', lw=1)  # Horizontal line
        self.ax.axvline(0, color='black', lw=1)  # Vertical line
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        # Plot initial cross markers without labels
        self.cross_marker1, = self.ax.plot([0], [0], marker="x", color="blue",
                                           label="PSD0 M2 Side")
        self.cross_marker2, = self.ax.plot([0], [0], marker="x", color="red",
                                           label="PSD1 M1 Side")

        # Add legend to the plot
        self.ax.legend(loc='upper right')  # Add legend and set its location

      # Create label to display moving average above the scrolledtext
        self.avg_display = tk.Label(self.root, text="Moving Average: ")    
        self.avg_display.pack(side=tk.TOP)

        # Create GUI layout
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.label1=tk.Label(self.root, text="Time                    X0      Y0       X1       Y1       σ_X0      σ_Y0    σ_X1    σ_Y1   Temp  ")
        self.label1.pack(side=tk.TOP,anchor="w")
        self.data_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=50, height=10)
       
        self.data_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create entry for moving average input
        self.avg_label = tk.Label(self.root, text="Moving Avg Window:")
        self.avg_label.pack(side=tk.LEFT)
        self.avg_input = tk.Entry(self.root)
        self.avg_input.insert(0, "10")
        self.avg_input.pack(side=tk.LEFT)


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
        self.moving_avg_window = 10  # Default moving average window size
        self.data_queue = deque(maxlen=self.moving_avg_window)

        self.file_name="data.txt"
    def stop_receiving_data(self):
        self.running = False  # Stop the data-receiving loop

    # Function to start receiving data
    def start_receiving_data(self):
        self.running = True  # Set the flag to True when starting
        self.moving_avg_window = int(self.avg_input.get())  # Get the moving average window size
        self.data_queue = deque(maxlen=self.moving_avg_window)  # Reset the deque with the new window size
        threading.Thread(target=self.receive_data, daemon=True).start()

    # Function to receive serial data
    def receive_data(self):
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        while self.running:
            data = get_serial_data(ser)  # Replace with actual serial reading
            self.parse_and_update(data)

    # Function to parse serial data and update the GUI
    def parse_and_update(self, data):
        # Parse the incoming data
        parsed_data = self.parse_serial_data(data)

        if parsed_data is not None:
            # Update the cross markers
            self.update_cross_markers(parsed_data)

            # Update the moving average
            self.average(parsed_data)

        # Append data with a timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        full_data = f"{timestamp}  {data}\n"
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

            # Ensure we have at least 9 values (x0, y0, x1, y1, sigma_x0, sigma_y0, sigma_x1, sigma_y1, temp)
            if len(values) >= 9:
                parsed_data = {
                    'x0': values[0],
                    'y0': values[1],
                    'x1': values[2],
                    'y1': values[3],
                    'sigma_x0': values[4],
                    'sigma_y0': values[5],
                    'sigma_x1': values[6],
                    'sigma_y1': values[7],
                    'temperature': values[8]
                }
                return parsed_data
            else:
                return None
        except ValueError:
            return None

    # Function to update the cross markers based on parsed data
    def update_cross_markers(self, data):
        x0, y0 = data.get('x0', 0), data.get('y0', 0)
        x1, y1 = data.get('x1', 0), data.get('y1', 0)

        # Update marker positions
        self.cross_marker1.set_data([x0], [y0])
        self.cross_marker2.set_data([x1], [y1])

        # Redraw plot
        self.canvas.draw()

    # Function to calculate and display moving averages
    def average(self, data):
        # Add current data to the queue
        self.data_queue.append(data)

        # If the queue is not full yet, skip calculation
        if len(self.data_queue) < self.moving_avg_window:
            return

        # Calculate moving averages
        avg_data = {key: np.mean([d[key] for d in self.data_queue]) for key in ['x0', 'y0', 'x1', 'y1']}
        avg_sigma = {key: np.sqrt(np.mean([d[key]**2 for d in
                                           self.data_queue]))/np.sqrt(len(self.data_queue)) for key in ['sigma_x0', 'sigma_y0', 'sigma_x1', 'sigma_y1']}

        # Display the moving averages
        avg_text = f"X0: {avg_data['x0']:.4e}, Y0: {avg_data['y0']:.4e}, X1:{avg_data['x1']:.4e}, Y1: {avg_data['y1']:.4e}"
        avg_sigma_text = f"σ_X0: {avg_sigma['sigma_x0']:.5e},σ_Y0:{avg_sigma['sigma_y0']:.5e}, σ_X1: {avg_sigma['sigma_x1']:.5e},σ_Y1: {avg_sigma['sigma_y1']:.5e}"
        self.avg_display.config(text=f"PSD Average: {avg_text} | {avg_sigma_text}\n{Distance}")

    # Function to save the moving averages along with Actuator values
    def save_data(self):
       # Ask for Actuator_1 and Actuator_2 values
        actuator_x = simpledialog.askfloat("Input", "Enter Actuator_x value:")
        actuator_y = simpledialog.askfloat("Input", "Enter Actuator_y value:")

        # Calculate current moving averages
        avg_data = {key: np.mean([d[key] for d in self.data_queue]) for key in ['x0', 'y0', 'x1', 'y1']}
        avg_sigma = {key: np.sqrt(np.mean([d[key]**2 for d in self.data_queue]))/np.sqrt(len(self.data_queue)) for key in ['sigma_x0', 'sigma_y0', 'sigma_x1', 'sigma_y1']}

        # Save data to a file
        full_path = filedialog.asksaveasfilename(initialfile=self.file_name,defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        self.file_name = os.path.basename(full_path)
        if self.file_name:
            write_header = not os.path.exists(self.file_name)  # Check if the file exists
            with open(self.file_name, 'a') as f:
                if write_header:
                     f.write("X0, Y0, X1, Y1, σ_X0, σ_Y0, σ_X1, σ_Y1,Actuator_x, Actuator_y\n")
                f.write(f"{avg_data['x0']:.4e}, {avg_data['y0']:.4e},{avg_data['x1']:.4e}, {avg_data['y1']:.4e}, ")
                f.write(f"{avg_sigma['sigma_x0']:.5e},{avg_sigma['sigma_y0']:.5e},{avg_sigma['sigma_x1']:.5e}, {avg_sigma['sigma_y1']:.5e}, ")
                f.write(f"{actuator_x:.4e}, {actuator_y:.4e}\n")

# Main function to run the app
def main():
    root = tk.Tk()
    app = SerialPlotApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
