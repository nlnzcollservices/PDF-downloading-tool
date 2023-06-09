import requests
import os
import signal
import time
import csv
from tkinter import Tk, Label, Button, filedialog, StringVar, Entry, Toplevel, ttk, Text
import urllib.parse
from datetime import datetime
from tkinter import messagebox
import traceback
import re
import urllib3
import pdfkit
urllib3.disable_warnings()

cancel_requested = False
csv_file_path = "webpages_downloads.csv"  # Path to the CSV file

current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M")

def download_webpage(url, save_directory, progress_text, file_count, csv_writer):
    """Downloads a web page from the given URL and saves it as a PDF file.
    
    Parameters:
        url (str): The URL of the web page to download.
        save_directory (str): The directory to save the PDF file.
    """
    # Generate a unique filename for the PDF
    filename = f"webpage_{url.split('/')[-1]}.pdf"
    save_path = os.path.join(save_directory, filename)
    
    try:
        # Convert the web page to PDF using pdfkit and wkhtmltopdf
        pdfkit.from_url(url, save_path)
        
        print(f"Web page saved as PDF: {save_path}")
        progress_text.insert('end', f"{save_path}: 100%\n")
        progress_text.see('end')  # Scroll to the latest progress
        progress_text.update_idletasks()  # Update the text widget
        csv_writer.writerow([url, save_path, "Done"])




    except Exception as e:
        print(f"Error converting web page to PDF: {url} ({str(e)})")
        progress_text.insert('end', f"Failed {url} {str(e)}")
        progress_text.see('end')  # Scroll to the latest progress
        progress_text.update_idletasks()  # Update the text widget
        csv_writer.writerow([url, save_path, "Failed", {str(e)}])
    file_count[0] += 1
    total_files = file_count[1]
    progress_text.insert('end', f"Processed: {file_count[0]} from {total_files}\n")

def get_processed_urls():

    """Retrieving list of original links from log csv file
    Returns:
        processed_urls(list) - list of successfully processed urls from the  csv log

    """
    processed_urls = []
    if os.path.isfile(csv_file_path):
        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip the header row
            for row in csv_reader:
                original_link = row[0]
                message = row[3]
                if message == 'Done':
                    processed_urls.append(original_link)
    return processed_urls

def process_urls(url_file_path, save_directory, progress_text, processed_urls):

    """Reading csv, getting processed links, directing urls which are not in list to process
    Parameters:
        url_file_path(str) - text file  with original urls one per line
        save_directory(str) - directory to save files
        progress_text(obj) - TK object which writing messages to text window
        processed_urls(list) - list of processed successfully urls from csv log file.
    Returns:
        None

    """

    print(processed_urls)
    with open(url_file_path, 'r') as file:
        urls = file.read().splitlines()

    file_count = [0, len(urls)]
   
    csv_header = ["Original Link", "Final Response Link", "Filename", "Status", "Run:" + formatted_datetime]
    try:
        with open(csv_file_path, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(csv_header)
            count_downloaded = 0

            for url in urls:
                print(url)
                url = url.rstrip(".")
                if not url in processed_urls:
                    if cancel_requested:  # Check if cancellation is requested
                        break  # Exit the loop if cancellation is requested

                    try:
                        download_webpage(url, save_directory, progress_text, file_count, csv_writer)
                    except Exception as e:
                        error_message = f"Error downloading {url}: {str(e)}"
                        progress_text.insert('end', error_message + "\n")
                        csv_writer.writerow([url, "", "", error_message])
                else:
                    progress_text.insert('end', url + " - Already downloaded\n")
                    progress_text.see('end')
                    count_downloaded +=1

                window.update()  # Update the GUI to prevent freezing
            print(file_count)
            if file_count[0]+count_downloaded == file_count[1]:
                progress_text.insert('end', "Finished.\n")
                progress_text.see('end')  # Scroll to the latest progress
                progress_text.update_idletasks()


    except PermissionError as e:
        error_message = f"Error writing to CSV file: {str(e)}.'\n'Please close the 'web_pages_download.csv' file'"
        progress_text.insert('end', error_message + "\n")
        progress_text.see('end')
        progress_text.update_idletasks()
        traceback.print_exc()  # Print the full error traceback to the console for debugging purposes


def start_download():

    """Managing process of starting downloading"""
    global cancel_requested
    cancel_requested = False  # Reset cancel_requested to False
    url_file_path = url_file_entry.get()
    save_directory = directory_var.get()

    processed_urls = get_processed_urls()

    progress_text.delete('1.0', 'end')  # Clear previous progress
    progress_text.insert('end', "Downloading...\n")
    progress_text.see('end') 
    process_urls(url_file_path, save_directory, progress_text ,processed_urls)

def cancel_download():

    """Breaking script when "Cancel button" pressed"""

    global cancel_requested
    cancel_requested = True

def browse_file():

    """Browse text file for GUI"""

    url_file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    url_file_entry.delete(0, 'end')
    url_file_entry.insert('end', url_file_path)

def browse_directory():

    """Brows save directory for GUI"""
    
    directory = filedialog.askdirectory()
    directory_var.set(directory)

def display_information():
    """Display information when the information button is clicked"""
    info_text = """This app allows you to download PDF files from a list of URLs.
                  1. Select a text file with the list of URLs.
                  2. Select a folder to save the downloaded files.
                  3. Click the 'Start Download' button to begin the download process.
                  4. The progress will be displayed in the text area.
                  5. You can cancel the download process by clicking the 'Cancel' button.
                  6. All information will be in "webpages_downloads.csv" file. 
                  7. If "webpages_downloads.csv" already exists new lines will be added there.
                  8. Links logged in "webpages_downloads.csv" will not be processed again.
                  9. Make sure that "webpages_downloads.csv" is not open when you run the app."""
    info_text = "\n".join(line.strip() for line in info_text.splitlines())
    messagebox.showinfo("Information", info_text)

# Create the GUI window
window = Tk()
window.geometry("800x500")  # Set the width and height of the window
window.title("PDF Downloader")

# URL file path
url_file_label = Label(window, text="Select the file with the list of URLs:", font=('Arial', 12, 'bold'), fg='#800000')
url_file_label.pack(anchor='w', padx=10)
url_info_label = Label(window, text="The app is accepting text file which contains links one per line", font=('Arial', 9), fg='#800000')
url_info_label.pack(anchor='w', padx=10)
url_file_entry = ttk.Entry(window, width=80)
url_file_entry.pack(anchor='w', padx=10)
browse_file_button = Button(window, text="Browse", command=browse_file)
browse_file_button.configure(font=('Arial', 12))
browse_file_button.pack(anchor='w', padx=10)

# Save directory
directory_label = Label(window, text="Select the folder to save the files:", font=('Arial', 12, 'bold'),  fg='#800000')
directory_label.pack(anchor='w', padx=10)
directory_var = StringVar()
directory_entry = ttk.Entry(window, textvariable=directory_var, width=80)
directory_entry.pack(anchor='w', padx=10)
browse_directory_button = Button(window, text="Browse", command=browse_directory)
browse_directory_button.configure(font=('Arial', 12))
browse_directory_button.pack(anchor='w', padx=10)

# Start and cancel download buttons
button_frame = ttk.Frame(window)
button_frame.pack()
download_button = Button(button_frame, text="Start Download", command=start_download)
download_button.configure(font=('Arial', 12))
download_button.pack(side='left', padx=10)
cancel_button = Button(button_frame, text="Cancel", command=cancel_download)
cancel_button.configure(font=('Arial', 12))
cancel_button.pack(side='left')
# Information button
info_button = Button(window, text="i", command=display_information, font=('Arial', 12, 'bold'))
info_button.place(x=470, y=10, width=30, height=30)

# Progress text
progress_label = Label(window, text="Progress:", font=('Arial', 12,'bold'), fg='#800000')
progress_label.pack()
progress_text = Text(window, height=30, width=110)
progress_text.pack()

# Run the GUI window
window.mainloop()
