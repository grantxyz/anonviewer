import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import messagebox, ttk
import os
import subprocess

ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("AnonViewer")
app.geometry("800x500")

try:
    app.iconbitmap(r'C:\Users\berkx\OneDrive\Desktop\anonviewer\icon1.ico')  # Set the icon using .ico file
except Exception as e:
    print(f"Error setting icon: {e}")


sort_criteria = tk.StringVar(value="Name")
include_background_apps = tk.BooleanVar(value=False)


def update_process_list():
    process_listbox.delete(0, tk.END)

    processes = [proc.info for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'memory_info', 'create_time', 'status'])]

    if not include_background_apps.get():
        processes = [proc for proc in processes if proc['status'] != psutil.STATUS_SLEEPING]  

    if sort_criteria.get() == "Name":
        processes.sort(key=lambda p: p['name'].lower())
    elif sort_criteria.get() == "PID":
        processes.sort(key=lambda p: p['pid'])
    elif sort_criteria.get() == "Memory":
        processes.sort(key=lambda p: p['memory_info'].rss, reverse=True)  
    elif sort_criteria.get() == "Newest":
        processes.sort(key=lambda p: p['create_time'], reverse=True)  
    elif sort_criteria.get() == "Oldest":
        processes.sort(key=lambda p: p['create_time'])  
    
    for proc in processes:
        process_listbox.insert(tk.END, f"{proc['name']} (PID: {proc['pid']})")

def show_process_details(event):
    selected_index = process_listbox.curselection()
    if not selected_index:
        return
    try:
        selected_text = process_listbox.get(selected_index[0])
        pid = int(selected_text.split('(PID: ')[1][:-1])
        proc = psutil.Process(pid)
        details = f"Name: {proc.name()}\nPID: {pid}\nCPU: {proc.cpu_percent()}%\nMemory: {proc.memory_info().rss / 1024 / 1024:.2f} MB\nPath: {proc.exe()}"
        details_label.configure(text=details)
        load_process_code(proc.exe()) 
    except Exception as e:
        details_label.configure(text=f"Error: {str(e)}")

def load_process_code(exe_path):
    if not exe_path or not os.path.exists(exe_path):
        code_viewer.delete("1.0", tk.END)
        code_viewer.insert(tk.END, "Cannot read process executable.\n")
        return

    try:
        with open(exe_path, "rb") as f:
            binary_data = f.read(256)  
            hex_data = ' '.join(f"{b:02X}" for b in binary_data)
            binary_data_str = ' '.join(f"{b:08b}" for b in binary_data)
            formatted_code = f"Hex:\n{hex_data}\n\nBinary:\n{binary_data_str}"
            code_viewer.delete("1.0", tk.END)
            code_viewer.insert(tk.END, formatted_code)
    except Exception as e:
        code_viewer.delete("1.0", tk.END)
        code_viewer.insert(tk.END, f"Error reading file: {str(e)}")

def kill_process():
    selected_index = process_listbox.curselection()
    if not selected_index:
        return
    try:
        selected_text = process_listbox.get(selected_index[0])
        pid = int(selected_text.split('(PID: ')[1][:-1])
        proc = psutil.Process(pid)
        proc.terminate()
        update_process_list()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to terminate process: {str(e)}")
def update_network_connections():
    network_listbox.delete(0, tk.END)

    connections = psutil.net_connections(kind='inet')
    
    for conn in connections:

        local_addr = conn.laddr
        remote_addr = conn.raddr if conn.raddr else ('', 0)
        status = conn.status
        pid = conn.pid

        network_listbox.insert(tk.END, f"Local: {local_addr} -> Remote: {remote_addr} | Status: {status} | PID: {pid}")

def execute_cmd():
    cmd = cmd_input.get()
    if not cmd:
        return
    try:
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        cmd_output.delete(1.0, tk.END)
        cmd_output.insert(tk.END, result.stdout)  
        if result.stderr:
            cmd_output.insert(tk.END, f"\nError: {result.stderr}")  
    except Exception as e:
        cmd_output.delete(1.0, tk.END)
        cmd_output.insert(tk.END, f"Error executing command: {str(e)}")

def show_system_info():
    try:
        system_info = f"CPU: {psutil.cpu_percent()}%\nMemory: {psutil.virtual_memory().percent}% used\nDisk: {psutil.disk_usage('/').percent}% used\nNetwork: {psutil.net_if_addrs()}"
        system_info_label.configure(text=system_info)
    except Exception as e:
        system_info_label.configure(text=f"Error: {str(e)}")

def monitor_ports():
    try:
        connections = psutil.net_connections(kind='inet')
        port_info = "\n".join([f"Local: {conn.laddr} -> Remote: {conn.raddr} | Status: {conn.status}" for conn in connections])
        port_info_label.configure(text=port_info)
    except Exception as e:
        port_info_label.configure(text=f"Error: {str(e)}")

notebook = ttk.Notebook(app)
notebook.pack(fill="both", expand=True)

task_manager_frame = ctk.CTkFrame(notebook)
notebook.add(task_manager_frame, text="Task Manager")

frame = ctk.CTkFrame(task_manager_frame)
frame.pack(side="left", padx=10, pady=10, fill="y")

process_listbox = tk.Listbox(frame, height=20, width=40)
process_listbox.pack(fill="both", expand=True)
process_listbox.bind("<<ListboxSelect>>", show_process_details)

info_frame = ctk.CTkFrame(task_manager_frame)
info_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

details_label = ctk.CTkLabel(info_frame, text="Select a process to see details", anchor="w", justify="left")
details_label.pack(fill="both", expand=True, padx=10, pady=10)

kill_button = ctk.CTkButton(info_frame, text="Kill Process", command=kill_process)
kill_button.pack(pady=10)

filter_label = ctk.CTkLabel(info_frame, text="Filter by:", anchor="w")
filter_label.pack(pady=5)

filter_menu = ctk.CTkOptionMenu(info_frame, values=["Name", "PID", "Memory", "Newest", "Oldest"], variable=sort_criteria, command=lambda _: update_process_list())
filter_menu.pack(pady=5)

background_apps_checkbox = ctk.CTkCheckBox(info_frame, text="Include Background Apps", variable=include_background_apps, onvalue=True, offvalue=False, command=update_process_list)
background_apps_checkbox.pack(pady=5)

system_info_frame = ctk.CTkFrame(notebook)
notebook.add(system_info_frame, text="System Info")

system_info_label = ctk.CTkLabel(system_info_frame, text="Loading system info...", anchor="w", justify="left")
system_info_label.pack(fill="both", expand=True, padx=10, pady=10)

refresh_system_info_button = ctk.CTkButton(system_info_frame, text="Refresh System Info", command=show_system_info)
refresh_system_info_button.pack(pady=10)

ports_frame = ctk.CTkFrame(notebook)
notebook.add(ports_frame, text="Port Monitoring")

port_info_label = ctk.CTkLabel(ports_frame, text="Monitoring ports...", anchor="w", justify="left")
port_info_label.pack(fill="both", expand=True, padx=10, pady=10)

refresh_ports_button = ctk.CTkButton(ports_frame, text="Refresh Ports Info", command=monitor_ports)
refresh_ports_button.pack(pady=10)

code_viewer_frame = ctk.CTkFrame(notebook)
notebook.add(code_viewer_frame, text="Code Viewer")

code_viewer = tk.Text(code_viewer_frame, wrap="word", height=20, width=80, bg="black", fg="lime")
code_viewer.pack(fill="both", expand=True, padx=10, pady=10)

network_frame = ctk.CTkFrame(notebook)
notebook.add(network_frame, text="Network")

network_listbox = tk.Listbox(network_frame, height=20, width=80)
network_listbox.pack(fill="both", expand=True, padx=10, pady=10)

refresh_button = ctk.CTkButton(network_frame, text="Refresh Network Connections", command=update_network_connections)
refresh_button.pack(pady=10)

cmd_frame = ctk.CTkFrame(notebook)
notebook.add(cmd_frame, text="CMD")

cmd_input_label = ctk.CTkLabel(cmd_frame, text="Enter Command:", anchor="w")
cmd_input_label.pack(pady=10, padx=10)

cmd_input = ctk.CTkEntry(cmd_frame, width=600)
cmd_input.pack(pady=5, padx=10)

cmd_execute_button = ctk.CTkButton(cmd_frame, text="Execute", command=execute_cmd)
cmd_execute_button.pack(pady=5)

cmd_output = tk.Text(cmd_frame, height=15, width=80, wrap="word", bg="black", fg="lime")
cmd_output.pack(pady=10, padx=10)

update_process_list()
show_system_info()
monitor_ports()

app.mainloop()       # made by @grantxyz on github and some other socials please dont mind the messy code this is one of my first projects
