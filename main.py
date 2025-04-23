import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import shutil  # Added for deleting folders
from datetime import datetime
from plyer import notification
import time
import threading
import pygame  # For sound effects
import winsound  # Alternative sound option for Windows

# Initialize pygame for sound
pygame.init()

# Global variables
pomodoro_running = False
pomodoro_paused = False
pause_time = 0
timer_thread = None
task_folder = None  # Currently selected folder

# Function to create a folder
def create_folder():
    folder_name = folder_entry.get()
    if folder_name:
        folder_path = os.path.join("task_folders", folder_name)
        if not os.path.exists(folder_path):  # Create the folder if it doesn't exist
            os.makedirs(folder_path)
            update_folder_list()  # Update the folder list
            folder_entry.delete(0, tk.END)  # Clear the input box
            messagebox.showinfo("Folder Created", f"Folder '{folder_name}' created successfully!")
            # Auto-select the newly created folder
            select_folder_by_name(folder_name)
        else:
            messagebox.showwarning("Folder Exists", f"Folder '{folder_name}' already exists.")
    else:
        messagebox.showwarning("Input Error", "Please enter a folder name.")

# Helper function to select folder by name
def select_folder_by_name(folder_name):
    for i in range(folder_listbox.size()):
        if folder_listbox.get(i) == folder_name:
            folder_listbox.selection_clear(0, tk.END)
            folder_listbox.selection_set(i)
            folder_listbox.see(i)
            select_folder()  # Call select_folder to update UI
            break

# New function to browse and add an existing folder
def browse_folder():
    folder_path = filedialog.askdirectory(title="Select Folder")
    if folder_path:
        folder_name = os.path.basename(folder_path)
        target_path = os.path.join("task_folders", folder_name)
        
        # Create a folder with the same name in our task_folders directory
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            update_folder_list()
            messagebox.showinfo("Folder Added", f"Folder '{folder_name}' added successfully!")
            # Auto-select the newly added folder
            select_folder_by_name(folder_name)
        else:
            messagebox.showwarning("Folder Exists", f"Folder '{folder_name}' already exists.")

# New function to delete a selected folder
def delete_folder():
    selected_folder = folder_listbox.curselection()
    if selected_folder:
        folder_name = folder_listbox.get(selected_folder[0])
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", 
                                      f"Are you sure you want to delete the folder '{folder_name}' and all its tasks?")
        
        if confirm:
            folder_path = os.path.join("task_folders", folder_name)
            try:
                # Delete the folder and all its contents
                shutil.rmtree(folder_path)
                
                # Update the folder list
                update_folder_list()
                
                # Update UI
                folder_label.config(text="💖 No folder selected 💖")
                task_listbox.delete(0, tk.END)
                task_count_label.config(text="Tasks: 0/0 completed")
                status_label.config(text="Status: Please select a folder first")
                task_entry.config(state='disabled')
                add_button.config(state='disabled')
                
                # Reset global task_folder
                global task_folder
                task_folder = None
                
                messagebox.showinfo("Folder Deleted", f"Folder '{folder_name}' has been deleted successfully!")
            except Exception as e:
                messagebox.showerror("Delete Error", f"Error deleting folder: {str(e)}")
    else:
        messagebox.showwarning("Selection Error", "Please select a folder to delete.")

# Function to select a folder
def select_folder():
    global task_folder
    selected_folder = folder_listbox.curselection()
    if selected_folder:
        folder_name = folder_listbox.get(selected_folder[0])
        folder_label.config(text=f"💖 Selected Folder: {folder_name} 💖")
        task_folder = os.path.join("task_folders", folder_name)
        
        # Update status label and enable task entry
        status_label.config(text=f"Status: Ready to add tasks to '{folder_name}'")
        task_entry.config(state='normal')
        add_button.config(state='normal')
        
        # Update the task list for the selected folder
        update_task_list()
    else:
        messagebox.showwarning("Selection Error", "Please select a folder.")

# Function to add a task
def add_task():
    task = task_entry.get()
    if task and task_folder:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_file = os.path.join(task_folder, "tasks.txt")
        with open(task_file, "a") as file:
            file.write(f"{task} | {timestamp} | Incomplete\n")
        
        # Update task listbox
        display_text = f"{task} - {timestamp} - Incomplete"
        task_listbox.insert(tk.END, display_text)
        task_entry.delete(0, tk.END)  # Clear the entry box
        
        # Play a gentle sound for task added
        play_sound("task_added")
        
        # Update task count
        update_task_count()
    else:
        if not task_folder:
            messagebox.showwarning("No Folder Selected", "Please select a folder first before adding a task.")
        else:
            messagebox.showwarning("Empty Task", "Please enter a task description.")

# Function to remove a task
def remove_task():
    try:
        selected_task_index = task_listbox.curselection()[0]
        task_listbox.delete(selected_task_index)
        task_file = os.path.join(task_folder, "tasks.txt")
        with open(task_file, "r") as file:
            lines = file.readlines()
        lines.pop(selected_task_index)
        with open(task_file, "w") as file:
            file.writelines(lines)
            
        # Update task count
        update_task_count()
    except IndexError:
        messagebox.showwarning("Selection Error", "Please select a task to remove.")

# Function to mark a task as completed
def complete_task():
    try:
        selected_task_index = task_listbox.curselection()[0]
        task_text = task_listbox.get(selected_task_index)
        
        # Check if task is already completed
        if "✔" in task_text or "- Complete" in task_text:
            messagebox.showinfo("Task Status", "This task is already completed!")
            return
            
        # Mark task as completed in the listbox
        task_listbox.itemconfig(selected_task_index, {'bg': 'lightgreen'})
        
        # Remove the old entry and add a new one with completion mark
        task_listbox.delete(selected_task_index)
        if "- Incomplete" in task_text:
            task_text = task_text.replace("- Incomplete", "- Complete ✔")
        else:
            task_text = f"{task_text} ✔"
        
        task_listbox.insert(selected_task_index, task_text)
        task_listbox.itemconfig(selected_task_index, {'bg': 'lightgreen'})
        
        # Update the tasks.txt file
        task_file = os.path.join(task_folder, "tasks.txt")
        if os.path.exists(task_file):
            with open(task_file, "r") as file:
                lines = file.readlines()
            
            # Replace "Incomplete" with "Complete" in the selected task line
            if selected_task_index < len(lines):
                parts = lines[selected_task_index].split(" | ")
                if len(parts) >= 3:
                    lines[selected_task_index] = f"{parts[0]} | {parts[1]} | Complete\n"
                
                with open(task_file, "w") as file:
                    file.writelines(lines)
                
                # Play completion sound
                play_sound("task_complete")
                
                # Update task count
                update_task_count()
    except IndexError:
        messagebox.showwarning("Selection Error", "Please select a task to mark as completed.")

# Function to update the task list based on the selected folder
def update_task_list():
    task_listbox.delete(0, tk.END)
    if task_folder:
        task_file = os.path.join(task_folder, "tasks.txt")
        if os.path.exists(task_file):
            with open(task_file, "r") as file:
                tasks = file.readlines()
                for task in tasks:
                    task_data = task.strip().split(" | ")
                    if len(task_data) >= 3:
                        task_name, timestamp, status = task_data[0], task_data[1], task_data[2]
                        display_text = f"{task_name} - {timestamp} - {status}"
                        
                        # Add completion mark
                        if status == "Complete":
                            display_text += " ✔"
                            
                        task_listbox.insert(tk.END, display_text)
                        
                        # Color completed tasks green
                        if status == "Complete":
                            task_listbox.itemconfig(tk.END-1, {'bg': 'lightgreen'})
        
        # Update task count
        update_task_count()

# Function to update task count
def update_task_count():
    if task_folder:
        total_tasks = task_listbox.size()
        completed_tasks = 0
        
        # Count completed tasks
        for i in range(total_tasks):
            if "✔" in task_listbox.get(i) or "- Complete" in task_listbox.get(i):
                completed_tasks += 1
        
        # Update the count label
        task_count_label.config(text=f"Tasks: {completed_tasks}/{total_tasks} completed")

# Play sound function
def play_sound(sound_type):
    try:
        if sound_type == "pomodoro_complete":
            winsound.Beep(1000, 500)  # Frequency, duration
            winsound.Beep(1200, 500)
            winsound.Beep(1500, 800)
        elif sound_type == "task_complete":
            winsound.Beep(800, 200)
            winsound.Beep(1000, 300)
        elif sound_type == "task_added":
            winsound.Beep(600, 100)
    except:
        # If winsound fails, try pygame as backup
        try:
            if sound_type == "pomodoro_complete":
                pygame.mixer.Sound("sounds/complete.wav").play()
            elif sound_type == "task_complete":
                pygame.mixer.Sound("sounds/tick.wav").play()
            elif sound_type == "task_added":
                pygame.mixer.Sound("sounds/add.wav").play()
        except:
            # If both fail, use the notification system without sound
            pass

# Fixed Pomodoro Timer (with thread-safe UI updates)
def update_timer_display(text):
    time_left_label.config(text=text)

# Function for Pomodoro Timer (threaded version)
def pomodoro_thread():
    global pomodoro_running, pomodoro_paused
    
    work_time = 25 * 60  # 25 minutes
    break_time = 5 * 60  # 5 minutes
    
    try:
        notification.notify(title="Pomodoro Timer", message="Work Time Started!", timeout=5)
    except Exception as e:
        print(f"Notification error: {e}")
    
    # Work period
    remaining_time = work_time
    while remaining_time > 0 and pomodoro_running:
        # Check if timer is paused
        if pomodoro_paused:
            mins, secs = divmod(remaining_time, 60)
            display_text = f"PAUSED: {mins:02}:{secs:02} - Work Time"
            root.after(0, lambda t=display_text: update_timer_display(t))
            time.sleep(0.5)
            continue
            
        mins, secs = divmod(remaining_time, 60)
        display_text = f"Time Left: {mins:02}:{secs:02} - Work Time"
        root.after(0, lambda t=display_text: update_timer_display(t))
        time.sleep(1)
        remaining_time -= 1
    
    if pomodoro_running:  # Only continue if not manually stopped
        # Play completion sound
        root.after(0, lambda: play_sound("pomodoro_complete"))
        
        try:
            notification.notify(title="Pomodoro Timer", message="Break Time Started!", timeout=5)
        except Exception as e:
            print(f"Notification error: {e}")
        
        # Break period
        remaining_time = break_time
        while remaining_time > 0 and pomodoro_running:
            # Check if timer is paused
            if pomodoro_paused:
                mins, secs = divmod(remaining_time, 60)
                display_text = f"PAUSED: {mins:02}:{secs:02} - Break Time"
                root.after(0, lambda t=display_text: update_timer_display(t))
                time.sleep(0.5)
                continue
                
            mins, secs = divmod(remaining_time, 60)
            display_text = f"Time Left: {mins:02}:{secs:02} - Break Time"
            root.after(0, lambda t=display_text: update_timer_display(t))
            time.sleep(1)
            remaining_time -= 1
        
        if pomodoro_running:  # If not manually stopped
            # Play completion sound
            root.after(0, lambda: play_sound("pomodoro_complete"))
            
            try:
                notification.notify(title="Pomodoro Timer", 
                                   message="Pomodoro Complete! Take a longer break or start a new session.", 
                                   timeout=10)
            except Exception as e:
                print(f"Notification error: {e}")
                
            root.after(0, lambda: update_timer_display("Pomodoro Complete!"))
            root.after(0, lambda: pomodoro_button.config(text="Start Pomodoro"))
            
            # Reset the state without using global declaration here
            # (since we already have it at the top of the function)
            pomodoro_running = False
            pomodoro_paused = False

# Function to start Pomodoro timer
def start_pomodoro():
    global pomodoro_running, pomodoro_paused, timer_thread
    
    if not pomodoro_running:
        pomodoro_running = True
        pomodoro_paused = False
        pomodoro_button.config(text="Stop Pomodoro")
        pause_button.config(text="Pause")
        
        # Start the timer in a separate thread
        timer_thread = threading.Thread(target=pomodoro_thread)
        timer_thread.daemon = True  # Make thread exit when main program exits
        timer_thread.start()
    else:
        # Stop the timer
        pomodoro_running = False
        pomodoro_paused = False
        pomodoro_button.config(text="Start Pomodoro")
        pause_button.config(text="Pause")
        time_left_label.config(text="Time Left: 00:00")

# Function to pause/resume Pomodoro timer
def pause_pomodoro():
    global pomodoro_paused
    
    if pomodoro_running:
        if not pomodoro_paused:
            pomodoro_paused = True
            pause_button.config(text="Resume")
        else:
            pomodoro_paused = False
            pause_button.config(text="Pause")

# Function to display current date and time
def update_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=current_time)
    root.after(1000, update_time)  # Update time every second

# Function to update the folder list
def update_folder_list():
    folder_listbox.delete(0, tk.END)
    if not os.path.exists("task_folders"):
        os.makedirs("task_folders")
    folder_names = os.listdir("task_folders")
    for folder in folder_names:
        if os.path.isdir(os.path.join("task_folders", folder)):
            folder_listbox.insert(tk.END, folder)

# Create the main window
root = tk.Tk()
root.title("Cute To-Do Tracker")  # Title of the window
root.geometry("600x750")  # Increased size for better display
root.config(bg="#FFB6C1")  # Light pink background

# Ensure the sounds directory exists
if not os.path.exists("sounds"):
    os.makedirs("sounds")

# Set the application icon if available
try:
    root.iconbitmap('cool.ico')  # Ensure the icon is in the same directory as the script
except:
    pass  # Skip if icon not found

# Create a sidebar for folder management
sidebar_frame = tk.Frame(root, bg="#FFD1DC", width=200, bd=2, relief=tk.GROOVE)
sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
sidebar_frame.pack_propagate(False)  # Prevent the frame from shrinking

# Folder section title
folder_section_label = tk.Label(sidebar_frame, text="💖 FOLDERS 💖", font=("Comic Sans MS", 12, "bold"), bg="#FFD1DC", fg="#8B008B")
folder_section_label.pack(pady=(10, 5))

# Frame for folder entry and buttons
folder_entry_frame = tk.Frame(sidebar_frame, bg="#FFD1DC")
folder_entry_frame.pack(pady=5, fill=tk.X, padx=5)

folder_entry_label = tk.Label(folder_entry_frame, text="New Folder:", font=("Comic Sans MS", 10), bg="#FFD1DC")
folder_entry_label.pack(anchor=tk.W)

folder_entry = tk.Entry(folder_entry_frame, width=20, font=("Comic Sans MS", 10), bd=2, relief="solid")
folder_entry.pack(fill=tk.X, pady=(0, 5))

# Folder buttons
folder_buttons_frame = tk.Frame(sidebar_frame, bg="#FFD1DC")
folder_buttons_frame.pack(pady=5, fill=tk.X, padx=5)

create_folder_button = tk.Button(folder_buttons_frame, text="Create", width=8, font=("Comic Sans MS", 9), command=create_folder, bg="#FFB6C1", relief="raised", bd=2)
create_folder_button.grid(row=0, column=0, padx=2)

browse_folder_button = tk.Button(folder_buttons_frame, text="Add Existing", width=10, font=("Comic Sans MS", 9), command=browse_folder, bg="#FFB6C1", relief="raised", bd=2)
browse_folder_button.grid(row=0, column=1, padx=2)

# Add Delete Folder button
delete_folder_button = tk.Button(sidebar_frame, text="Delete Folder 🗑️", width=15, font=("Comic Sans MS", 9), 
                              command=delete_folder, bg="#FF9999", relief="raised", bd=2)
delete_folder_button.pack(pady=5)

# Folder list with scrollbar
folder_list_frame = tk.Frame(sidebar_frame, bg="#FFD1DC")
folder_list_frame.pack(pady=5, fill=tk.BOTH, expand=True, padx=5)

folder_listbox = tk.Listbox(folder_list_frame, width=20, font=("Comic Sans MS", 10), bd=2, relief="solid", highlightthickness=2)
folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
folder_listbox.config(bg="#FEE2E2", selectbackground="#FF6B81")

folder_scrollbar = tk.Scrollbar(folder_list_frame)
folder_listbox.config(yscrollcommand=folder_scrollbar.set)
folder_scrollbar.config(command=folder_listbox.yview)
folder_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

select_folder_button = tk.Button(sidebar_frame, text="Select Folder 💖", width=15, font=("Comic Sans MS", 10), command=select_folder, bg="#FFB6C1", relief="raised", bd=3)
select_folder_button.pack(pady=10)

folder_label = tk.Label(sidebar_frame, text="💖 No folder selected 💖", font=("Comic Sans MS", 9), bg="#FFD1DC", fg="#8B008B", wraplength=180)
folder_label.pack(pady=5)

# Create main content area
main_frame = tk.Frame(root, bg="#FFB6C1")
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# Status label - shows which folder is active for adding tasks
status_label = tk.Label(main_frame, text="Status: Please select a folder first", font=("Comic Sans MS", 10), bg="#FFB6C1", fg="#8B008B")
status_label.pack(pady=(10, 5), anchor=tk.W)

# Task input area
task_label = tk.Label(main_frame, text="💖 Add New Task 💖", font=("Comic Sans MS", 12, "bold"), bg="#FFB6C1")
task_label.pack(pady=(5, 0))

task_entry_frame = tk.Frame(main_frame, bg="#FFB6C1")
task_entry_frame.pack(fill=tk.X, pady=5)

task_entry = tk.Entry(task_entry_frame, width=40, font=("Comic Sans MS", 11), bd=2, relief="solid", state='disabled')
task_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

add_button = tk.Button(task_entry_frame, text="Add Task", width=10, font=("Comic Sans MS", 10), command=add_task, bg="#FFB6C1", relief="raised", bd=3, state='disabled')
add_button.pack(side=tk.RIGHT)

# Task management buttons
button_frame = tk.Frame(main_frame, bg="#FFB6C1")
button_frame.pack(pady=5, fill=tk.X)

remove_button = tk.Button(button_frame, text="Remove Task", width=15, font=("Comic Sans MS", 10), command=remove_task, bg="#FFB6C1", relief="raised", bd=3)
remove_button.pack(side=tk.LEFT, padx=5)

complete_button = tk.Button(button_frame, text="Complete Task ✔", width=15, font=("Comic Sans MS", 10), command=complete_task, bg="#FFB6C1", relief="raised", bd=3)
complete_button.pack(side=tk.RIGHT, padx=5)

# Task count label
task_count_label = tk.Label(main_frame, text="Tasks: 0/0 completed", font=("Comic Sans MS", 10), bg="#FFB6C1", fg="#8B008B")
task_count_label.pack(pady=5, anchor=tk.W)

# Listbox to display tasks with girly colors
task_list_label = tk.Label(main_frame, text="💖 Task List 💖", font=("Comic Sans MS", 12, "bold"), bg="#FFB6C1")
task_list_label.pack(pady=(5, 0))

task_list_frame = tk.Frame(main_frame, bg="#FFB6C1")
task_list_frame.pack(pady=5, fill=tk.BOTH, expand=True)

task_listbox = tk.Listbox(task_list_frame, width=50, height=10, selectmode=tk.SINGLE, font=("Comic Sans MS", 10), bd=2, relief="solid", highlightthickness=2)
task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
task_listbox.config(bg="#FEE2E2", selectbackground="#FF6B81")  # Soft pink background and selection color

task_scrollbar = tk.Scrollbar(task_list_frame)
task_listbox.config(yscrollcommand=task_scrollbar.set)
task_scrollbar.config(command=task_listbox.yview)
task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Pomodoro timer section
pomodoro_frame = tk.Frame(main_frame, bg="#FFC0CB", bd=2, relief=tk.GROOVE)
pomodoro_frame.pack(pady=10, fill=tk.X)

pomodoro_label = tk.Label(pomodoro_frame, text="💖 Pomodoro Timer 💖", font=("Comic Sans MS", 12, "bold"), bg="#FFC0CB", fg="#8B008B")
pomodoro_label.pack(pady=5)

time_left_label = tk.Label(pomodoro_frame, text="Time Left: 00:00", font=("Comic Sans MS", 14), bg="#FFC0CB", fg="#8B008B")
time_left_label.pack(pady=5)

pomodoro_buttons_frame = tk.Frame(pomodoro_frame, bg="#FFC0CB")
pomodoro_buttons_frame.pack(pady=10)

pomodoro_button = tk.Button(pomodoro_buttons_frame, text="Start Pomodoro", width=15, font=("Comic Sans MS", 10), command=start_pomodoro, bg="#FFB6C1", relief="raised", bd=3)
pomodoro_button.grid(row=0, column=0, padx=10)

pause_button = tk.Button(pomodoro_buttons_frame, text="Pause", width=15, font=("Comic Sans MS", 10), command=pause_pomodoro, bg="#FFB6C1", relief="raised", bd=3)
pause_button.grid(row=0, column=1, padx=10)

# Label to display the current date and time
time_label = tk.Label(main_frame, text="", font=("Comic Sans MS", 10), bg="#FFB6C1", fg="#8B008B")
time_label.pack(pady=5, anchor=tk.SE)

# Update folder list initially
update_folder_list()

# Start updating the time
update_time()

# Instructions for double-click functionality
def folder_double_click(event):
    select_folder()

folder_listbox.bind('<Double-1>', folder_double_click)

# Make sure task_folders directory exists
if not os.path.exists("task_folders"):
    os.makedirs("task_folders")

# Start the main event loop
root.mainloop()
