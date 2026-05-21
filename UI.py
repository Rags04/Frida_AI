import customtkinter
import threading
import subprocess
import os
import signal
import platform
import shutil
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import filedialog
from email.message import EmailMessage
from fpdf import FPDF
from pathlib import Path
from adb_pywrapper.adb_device import AdbDevice
from Frida_script import BYPASS_SCRIPTS


def find_executable(name: str):
    """Return the full path to an executable or None if not found."""
    result = shutil.which(name)
    if result:
        return result
    if os.name == 'nt' and not name.lower().endswith('.exe'):
        return shutil.which(f"{name}.exe")
    return None


def is_command_available(name: str) -> bool:
    return find_executable(name) is not None


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class FridaAutomationUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1000x700")
        self.root.title("Frida Automation Tool")
        
        self.selected_device = None
        self.selected_script = None
        self.selected_package = None
        self.selected_apk = None
        
        # Process tracking for stop functionality
        self.current_process = None
        self.is_running = False
        
        self.setup_ui()
        self.refresh_devices()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        self.root.minsize(1100, 720)

        # Main container
        main_frame = customtkinter.CTkFrame(self.root, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Header
        header_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        title_label = customtkinter.CTkLabel(
            header_frame,
            text="Frida Automation Tool",
            font=customtkinter.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=(10, 0))

        subtitle_label = customtkinter.CTkLabel(
            header_frame,
            text="Manage devices, bypass scripts, APK installs and deep link tests from one dashboard.",
            font=customtkinter.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(4, 0))

        self.status_label = customtkinter.CTkLabel(
            header_frame,
            text="Ready",
            font=customtkinter.CTkFont(size=12, weight="bold")
        )
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=(0, 10))

        # ============ LEFT PANEL - DEVICES ============
        left_frame = customtkinter.CTkFrame(main_frame, corner_radius=12)
        left_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        device_label = customtkinter.CTkLabel(
            left_frame,
            text="Connected Devices",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        device_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        device_box_frame = customtkinter.CTkFrame(left_frame, fg_color="transparent")
        device_box_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        device_box_frame.grid_rowconfigure(0, weight=1)
        device_box_frame.grid_columnconfigure(0, weight=1)

        self.device_listbox = tk.Listbox(
            device_box_frame,
            width=32,
            height=8,
            activestyle="dotbox",
            exportselection=False,
            selectmode=tk.SINGLE
        )
        self.device_listbox.grid(row=0, column=0, sticky="nsew")
        self.device_listbox.bind("<<ListboxSelect>>", self.on_device_selected)

        device_scrollbar = tk.Scrollbar(device_box_frame, command=self.device_listbox.yview)
        device_scrollbar.grid(row=0, column=1, sticky="ns")
        self.device_listbox.configure(yscrollcommand=device_scrollbar.set)

        self.device_info_label = customtkinter.CTkLabel(
            left_frame,
            text="No device selected",
            text_color="gray",
            anchor="w",
            justify="left"
        )
        self.device_info_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        refresh_btn = customtkinter.CTkButton(
            left_frame,
            text="🔄 Refresh Devices",
            command=self.refresh_devices,
            corner_radius=10
        )
        refresh_btn.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        # ============ CENTER PANEL - SCRIPTS & PACKAGES ============
        center_frame = customtkinter.CTkFrame(main_frame, corner_radius=12)
        center_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        # Script card
        script_frame = customtkinter.CTkFrame(center_frame, corner_radius=12)
        script_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        script_frame.grid_columnconfigure(0, weight=1)

        scripts_label = customtkinter.CTkLabel(
            script_frame,
            text="Frida Bypass Scripts",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        scripts_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.script_var = customtkinter.StringVar(value="Select a script...")
        script_names = list(BYPASS_SCRIPTS.keys())
        self.script_dropdown = customtkinter.CTkOptionMenu(
            script_frame,
            variable=self.script_var,
            values=script_names,
            command=self.on_script_selected,
            width=400
        )
        self.script_dropdown.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.selected_script_label = customtkinter.CTkLabel(
            script_frame,
            text="No script selected",
            text_color="gray",
            anchor="w",
            justify="left"
        )
        self.selected_script_label.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="ew")

        self.script_description = customtkinter.CTkLabel(
            script_frame,
            text="Select a script to see its description and run options.",
            text_color="gray",
            justify="left",
            wraplength=520
        )
        self.script_description.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        # Package card
        packages_card = customtkinter.CTkFrame(center_frame, corner_radius=12)
        packages_card.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        packages_card.grid_rowconfigure(1, weight=1)
        packages_card.grid_columnconfigure(0, weight=1)

        packages_label = customtkinter.CTkLabel(
            packages_card,
            text="Installed Packages",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        packages_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        packages_frame = customtkinter.CTkFrame(packages_card, fg_color="transparent")
        packages_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        packages_frame.grid_rowconfigure(0, weight=1)
        packages_frame.grid_columnconfigure(0, weight=1)

        self.packages_listbox = tk.Listbox(
            packages_frame,
            width=90,
            height=20,
            activestyle="dotbox",
            exportselection=False,
            selectmode=tk.SINGLE
        )
        self.packages_listbox.grid(row=0, column=0, sticky="nsew")
        self.packages_listbox.bind("<<ListboxSelect>>", self.on_package_selected)

        package_scrollbar = tk.Scrollbar(packages_frame, command=self.packages_listbox.yview)
        package_scrollbar.grid(row=0, column=1, sticky="ns")
        self.packages_listbox.configure(yscrollcommand=package_scrollbar.set)

        self.package_note = customtkinter.CTkLabel(
            packages_card,
            text="Select a package below before running the selected Frida script.",
            text_color="gray",
            justify="left"
        )
        self.package_note.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        refresh_pkg_btn = customtkinter.CTkButton(
            packages_card,
            text="📦 Load Packages from Device",
            command=self.load_packages,
            corner_radius=10
        )
        refresh_pkg_btn.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        # ============ RIGHT PANEL - ACTIONS ============
        right_frame = customtkinter.CTkFrame(main_frame, corner_radius=12)
        right_frame.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        right_frame.grid_rowconfigure(8, weight=1)

        action_label = customtkinter.CTkLabel(
            right_frame,
            text="Actions",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        action_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 8))

        run_frida_btn = customtkinter.CTkButton(
            right_frame,
            text="▶ Run Script",
            command=self.run_frida_script,
            height=40,
            fg_color="green",
            corner_radius=10
        )
        run_frida_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        install_apk_btn = customtkinter.CTkButton(
            right_frame,
            text="📦 Install APK",
            command=self.install_apk,
            height=40,
            fg_color="#4CAF50",
            corner_radius=10
        )
        install_apk_btn.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        test_deeplinks_btn = customtkinter.CTkButton(
            right_frame,
            text="🔗 Test Deep Links",
            command=self.test_deep_links,
            height=40,
            fg_color="#FF6B35",
            corner_radius=10
        )
        test_deeplinks_btn.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        generate_pdf_btn = customtkinter.CTkButton(
            right_frame,
            text="📄 Generate PDF Report",
            command=self.generate_pdf_report,
            height=40,
            fg_color="#4F8EF7",
            corner_radius=10
        )
        generate_pdf_btn.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        create_email_btn = customtkinter.CTkButton(
            right_frame,
            text="✉️ Create Outlook Template",
            command=self.create_email_template,
            height=40,
            fg_color="#6A5ACD",
            corner_radius=10
        )
        create_email_btn.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        # Stop Execution button
        self.stop_btn = customtkinter.CTkButton(
            right_frame,
            text="⏹ Stop Execution",
            command=self.stop_execution,
            height=40,
            fg_color="#DC3545",
            corner_radius=10,
            state="disabled"
        )
        self.stop_btn.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        action_note = customtkinter.CTkLabel(
            right_frame,
            text="Tip: Refresh devices and load packages before running scripts.",
            text_color="gray",
            justify="left"
        )
        action_note.grid(row=7, column=0, padx=10, pady=(8, 10), sticky="ew")

        # ============ BOTTOM PANEL - LOGS ============
        bottom_frame = customtkinter.CTkFrame(main_frame, corner_radius=12)
        bottom_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        bottom_frame.grid_rowconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)

        log_label = customtkinter.CTkLabel(
            bottom_frame,
            text="Execution Logs",
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        log_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.log_textbox = customtkinter.CTkTextbox(bottom_frame, height=140)
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_textbox.configure(state="disabled")
    
    def refresh_devices(self):
        """Refresh list of connected devices"""
        self.log_message("Scanning for connected devices...")
        threading.Thread(target=self._refresh_devices_thread, daemon=True).start()
    
    def _refresh_devices_thread(self):
        """Thread function to refresh devices"""
        try:
            devices = []
            
            # Try method 1: AdbDevice.list_devices()
            try:
                devices = AdbDevice.list_devices()
                self.log_message(f"[DEBUG] AdbDevice.list_devices() returned: {devices} (type: {type(devices)})")
                
                # Handle different return types
                if isinstance(devices, dict):
                    # If it returns a dict, get the keys
                    devices = list(devices.keys())
                elif not isinstance(devices, list):
                    devices = list(devices) if devices else []
            except Exception as e1:
                self.log_message(f"[DEBUG] Method 1 failed: {str(e1)}")
                devices = []
            
            # Try method 2: Use subprocess with adb command directly
            if not devices:
                adb_exe = find_executable("adb")
                if not adb_exe:
                    self.log_message("✗ ADB executable not found in PATH for device discovery.")
                else:
                    try:
                        result = subprocess.run([adb_exe, "devices"], capture_output=True, text=True, timeout=10)
                        lines = result.stdout.strip().split('\n')
                        devices = []

                        for line in lines[1:]:  # Skip first line "List of attached devices"
                            if line.strip() and 'device' in line.lower():
                                device_id = line.split()[0].strip()
                                if device_id and device_id != 'List':
                                    devices.append(device_id)

                        self.log_message(f"[DEBUG] ADB command returned devices: {devices}")
                    except Exception as e2:
                        self.log_message(f"[DEBUG] Method 2 (subprocess) failed: {str(e2)}")
            
            # Update UI
            self.device_listbox.delete(0, tk.END)
            
            if devices:
                for device in devices:
                    self.device_listbox.insert(tk.END, device)
                self.selected_device = devices[0]
                self.device_listbox.selection_set(0)
                self.device_info_label.configure(text=f"Selected device: {self.selected_device}")
                self.log_message(f"✓ Found {len(devices)} device(s): {devices}")
            else:
                self.selected_device = None
                self.device_info_label.configure(text="No device selected")
                self.device_listbox.insert(tk.END, "No devices connected")
                self.log_message("✗ No devices found. Please check USB connection and ensure ADB is installed.")
        except Exception as e:
            self.log_message(f"✗ Critical error refreshing devices: {str(e)}")
            self.device_listbox.delete(0, tk.END)
            self.device_listbox.insert(tk.END, f"Error: {str(e)}")
            self.device_info_label.configure(text="No device selected")
    
    def on_script_selected(self, choice):
        """Handle script selection from dropdown"""
        self.selected_script = choice
        if choice in BYPASS_SCRIPTS:
            description = BYPASS_SCRIPTS[choice]["description"]
            self.script_description.configure(text=description)
            self.selected_script_label.configure(text=f"Selected script: {choice}")
            self.status_label.configure(text=f"Ready to run: {choice}")
            self.log_message(f"Script selected: {choice}")
        else:
            self.selected_script_label.configure(text="No script selected")
            self.script_description.configure(text="Select a script to see its description and run options.")
    
    def load_packages(self):
        """Load installed packages from selected device"""
        if not self.selected_device:
            messagebox.showerror("Error", "No device selected. Please refresh devices first.")
            return
        
        self.log_message(f"Loading packages from {self.selected_device}...")
        threading.Thread(target=self._load_packages_thread, daemon=True).start()
    
    def _load_packages_thread(self):
        """Thread function to load packages"""
        try:
            packages = []
            
            # Try method 1: Using AdbDevice
            try:
                adb_device = AdbDevice(device=self.selected_device)
                result = adb_device.shell('pm list packages')
                self.log_message(f"[DEBUG] AdbDevice.shell() returned: {type(result)}")
                
                if result and hasattr(result, 'output'):
                    packages = [line.replace("package:", "").strip() 
                               for line in result.output.split('\n') 
                               if line.strip() and line.startswith("package:")]
            except Exception as e1:
                self.log_message(f"[DEBUG] Method 1 (AdbDevice) failed: {str(e1)}")
            
            # Try method 2: Use subprocess with adb command directly
            if not packages:
                adb_exe = find_executable("adb")
                if not adb_exe:
                    self.log_message("✗ ADB executable not found in PATH for package listing.")
                else:
                    try:
                        result = subprocess.run([adb_exe, "-s", self.selected_device, "shell", "pm", "list", "packages"], capture_output=True, text=True, timeout=30)

                        if result.returncode == 0:
                            packages = [line.replace("package:", "").strip()
                                       for line in result.stdout.split('\n')
                                       if line.strip() and line.startswith("package:")]
                            self.log_message(f"[DEBUG] Subprocess method returned {len(packages)} packages")
                    except Exception as e2:
                        self.log_message(f"[DEBUG] Method 2 (subprocess) failed: {str(e2)}")
            
            # Update UI
            self.packages_listbox.delete(0, tk.END)
            self.selected_package = None
            
            if packages:
                packages_sorted = sorted(packages)
                for pkg in packages_sorted:
                    self.packages_listbox.insert(tk.END, pkg)
                self.selected_package = packages_sorted[0]
                self.packages_listbox.selection_set(0)
                self.package_note.configure(text=f"Selected package: {self.selected_package}")
                self.status_label.configure(text=f"Packages loaded: {len(packages_sorted)}")
                self.log_message(f"✓ Loaded {len(packages)} packages")
            else:
                self.packages_listbox.insert(tk.END, "No packages found or ADB error")
                self.selected_package = None
                self.package_note.configure(text="No package selected")
                self.log_message("✗ No packages found. Check device connection.")
        except Exception as e:
            self.log_message(f"✗ Error loading packages: {str(e)}")
            self.packages_listbox.delete(0, tk.END)
            self.packages_listbox.insert(tk.END, f"Error: {str(e)}")
    
    def run_frida_script(self):
        """Run selected Frida script on device"""
        if not self.selected_device:
            messagebox.showerror("Error", "No device selected")
            return
        
        if not self.selected_script or self.selected_script == "Select a script...":
            messagebox.showerror("Error", "No script selected")
            return
        
        if not self.selected_package:
            messagebox.showerror("Error", "No target app selected. Please load packages and select one.")
            return
        
        script_content = BYPASS_SCRIPTS[self.selected_script]["script"]
        self.log_message(f"Injecting script '{self.selected_script}' into app: {self.selected_package}...")
        
        threading.Thread(
            target=self._run_frida_script_thread,
            args=(script_content, self.selected_package),
            daemon=True
        ).start()
    
    def _run_frida_script_thread(self, script_content, target_package):
        """Thread function to run Frida script"""
        self._update_button_state(True)
        try:
            frida_exe = find_executable("frida")
            frida_ps_exe = find_executable("frida-ps")
            if not frida_exe or not frida_ps_exe:
                self.log_message("✗ Frida command line tools not found. Install with: pip install frida-tools")
                self.log_message("Then install Frida server on your device from: https://github.com/vfsfitvnm/frida-il2cpp-bridge/releases")
                return

            # Check if device is connected via Frida
            device_check = subprocess.run([frida_ps_exe, "-U"], capture_output=True, text=True, timeout=10)
            if device_check.returncode != 0:
                self.log_message(f"✗ Device not accessible via Frida")
                self.log_message("Make sure:")
                self.log_message("1. USB debugging is enabled on the device")
                self.log_message("2. Device is authorized (check 'adb devices')")
                self.log_message("3. Frida server is running on the device")
                self.log_message("4. Device is rooted or has Frida server installed via Magisk")
                return

            # Check if target app is running
            self.log_message(f"Checking if {target_package} is running...")
            ps_result = subprocess.run([frida_ps_exe, "-U"], capture_output=True, text=True, timeout=10)

            if ps_result.returncode == 0 and target_package in ps_result.stdout:
                self.log_message(f"✓ App {target_package} is running. Attaching with -n.")
                launch_flag = '-n'
            else:
                self.log_message(f"⚠️ App {target_package} not currently running. Spawning with -f.")
                launch_flag = '-f'

            # Save script to temp file with proper name based on selected script
            script_filename = f"{self.selected_script.replace(' ', '_')}.js"
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Run frida command using -U and the correct launch flag
            cmd = [frida_exe, "-U", launch_flag, target_package, "-l", script_filename]
            self.log_message(f"[DEBUG] Running command: {' '.join(cmd)}")
            # Start process in its own group so we can kill the group later
            if os.name == 'nt':
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
            self.status_label.configure(text="Executing script...")
            
            stdout, stderr = self.current_process.communicate()

            if self.current_process.returncode == 0:
                self.log_message(f"✓ Script executed successfully on {target_package}")
            elif self.current_process.returncode == -15:  # SIGTERM from kill
                self.log_message(f"⚠️ Script execution was stopped")
            else:
                self.log_message(f"✗ Script execution failed (exit code {self.current_process.returncode})")

            if stdout:
                self.log_message(f"Output:\n{stdout.strip()}")
            if stderr:
                self.log_message(f"Error Output:\n{stderr.strip()}")
        except subprocess.TimeoutExpired:
            self.log_message("✗ Script execution timeout")
        except Exception as e:
            self.log_message(f"✗ Error running script: {str(e)}")
        finally:
            self.current_process = None
            self._update_button_state(False)
    
    def is_windows(self):
        """Check if running on Windows"""
        import platform
        return platform.system() == "Windows"

    def install_apk(self):
        """Open file dialog and install selected APK on the device"""
        if not self.selected_device:
            messagebox.showerror("Error", "No device selected. Please refresh devices first.")
            return

        apk_path = filedialog.askopenfilename(
            title="Select APK file to install",
            filetypes=[("Android APK", "*.apk")]
        )

        if not apk_path:
            return

        self.selected_apk = apk_path
        self.log_message(f"Selected APK: {self.selected_apk}")
        threading.Thread(target=self._install_apk_thread, args=(apk_path,), daemon=True).start()

    def _install_apk_thread(self, apk_path):
        """Thread function to install APK on the selected device"""
        self._update_button_state(True)
        try:
            if not apk_path or not apk_path.lower().endswith('.apk'):
                self.log_message("✗ Selected file is not an APK.")
                return

            adb_exe = find_executable("adb")
            if not adb_exe:
                self.log_message("✗ ADB executable not found in PATH for APK installation.")
                return

            self.log_message(f"Installing APK on device {self.selected_device}: {apk_path}")
            cmd = [adb_exe, "-s", self.selected_device, "install", "-r", apk_path]
            self.log_message(f"[DEBUG] Running command: {' '.join(cmd)}")
            if os.name == 'nt':
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
            self.status_label.configure(text="Installing APK...")
            
            stdout, stderr = self.current_process.communicate()

            if self.current_process.returncode == 0:
                self.log_message(f"✓ APK installed successfully: {apk_path}")
            elif self.current_process.returncode == -15:
                self.log_message(f"⚠️ APK installation was stopped")
            else:
                self.log_message(f"✗ APK installation failed (exit code {self.current_process.returncode})")

            if stdout:
                self.log_message(f"Output:\n{stdout.strip()}")
            if stderr:
                self.log_message(f"Error Output:\n{stderr.strip()}")
        except subprocess.TimeoutExpired:
            self.log_message("✗ APK installation timed out")
        except Exception as e:
            self.log_message(f"✗ Error installing APK: {str(e)}")
        finally:
            self.current_process = None
            self._update_button_state(False)
    
    def on_package_selected(self, event=None):
        """Handle package selection from the listbox"""
        selection = self.packages_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_package = self.packages_listbox.get(index)
            self.package_note.configure(text=f"Selected package: {self.selected_package}")
            self.status_label.configure(text=f"Package selected: {self.selected_package}")
            self.log_message(f"Package selected: {self.selected_package}")

    def on_device_selected(self, event=None):
        """Handle device selection from the device listbox"""
        selection = self.device_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_device = self.device_listbox.get(index)
            self.device_info_label.configure(text=f"Selected device: {self.selected_device}")
            self.status_label.configure(text=f"Device selected: {self.selected_device}")
            self.log_message(f"Device selected: {self.selected_device}")

    def generate_pdf_report(self):
        """Generate a PDF report from current UI state"""
        threading.Thread(target=self._generate_pdf_report_thread, daemon=True).start()
    
    def _generate_pdf_report_thread(self):
        try:
            report_path = "frida_report.pdf"
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Frida Automation Report", ln=True, align="C")
            pdf.ln(5)
            pdf.set_font("Helvetica", size=11)
            
            device_lines = list(self.device_listbox.get(0, tk.END))
            device_text = "\n".join(device_lines).strip() or "No devices connected"
            selected_script = self.selected_script or "None"
            script_description = BYPASS_SCRIPTS.get(self.selected_script, {}).get("description", "No description")
            package_lines = [self.packages_listbox.get(idx) for idx in range(self.packages_listbox.size())]
            packages_text = "\n".join(package_lines).strip() or "No packages loaded"
            logs_text = self.log_textbox.get("1.0", "end").strip() or "No logs available"
            
            pdf.cell(0, 8, f"Connected Device(s):", ln=True)
            pdf.set_font("Helvetica", size=10)
            for line in device_text.splitlines() or ["No devices connected"]:
                pdf.multi_cell(0, 6, f"  {line}")
            pdf.ln(3)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Selected Frida Script:", ln=True)
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, f"{selected_script}")
            pdf.multi_cell(0, 6, f"Description: {script_description}")
            pdf.ln(3)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Installed Packages:", ln=True)
            pdf.set_font("Helvetica", size=10)
            for line in packages_text.splitlines()[:50]:
                pdf.multi_cell(0, 6, f"  {line}")
            if len(packages_text.splitlines()) > 50:
                pdf.multi_cell(0, 6, "  ... list truncated ...")
            pdf.ln(3)
            
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Execution Logs:", ln=True)
            pdf.set_font("Helvetica", size=10)
            for line in logs_text.splitlines()[-60:]:
                pdf.multi_cell(0, 6, f"  {line}")
            
            pdf.output(report_path)
            self.log_message(f"✓ PDF report generated: {report_path}")
        except Exception as e:
            self.log_message(f"✗ Error generating PDF report: {str(e)}")
    
    def create_email_template(self):
        """Create an Outlook-compatible email template file (.eml)"""
        threading.Thread(target=self._create_email_template_thread, daemon=True).start()
    
    def _create_email_template_thread(self):
        try:
            report_path = "frida_report.pdf"
            subject = "Frida Automation Report"
            device_lines = list(self.device_listbox.get(0, tk.END))
            device_text = "\n".join(device_lines).strip() or "No device connected"
            selected_script = self.selected_script or "None"
            body = (
                f"Hello,\n\n"
                f"Please find the attached Frida automation report.\n\n"
                f"Connected Devices:\n{device_text}\n\n"
                f"Selected Script: {selected_script}\n"
                f"Please review the attached report for details.\n\n"
                f"Regards,\nFrida Automation Tool"
            )

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = "sender@example.com"
            msg["To"] = "recipient@example.com"
            msg.set_content(body)

            try:
                with open(report_path, "rb") as fp:
                    pdf_bytes = fp.read()
                msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=report_path)
            except FileNotFoundError:
                self.log_message(f"⚠️ PDF report not found at {report_path}. Email template created without attachment.")

            eml_path = "frida_report_email.eml"
            with open(eml_path, "wb") as f:
                f.write(msg.as_bytes())

            self.log_message(f"✓ Outlook email template created: {eml_path}")
        except Exception as e:
            self.log_message(f"✗ Error creating Outlook email template: {str(e)}")
    
    def test_deep_links(self):
        """Test deep links by sending intents and monitoring with Frida script"""
        if not self.selected_device:
            messagebox.showerror("Error", "No device selected. Please refresh devices first.")
            return
        
        if not self.selected_package:
            messagebox.showerror("Error", "No target app selected. Please load packages and select one.")
            return
        
        # Create deep link testing dialog
        dialog = customtkinter.CTkToplevel(self.root)
        dialog.geometry("600x400")
        dialog.title("Test Deep Links")
        
        # Title
        title_label = customtkinter.CTkLabel(
            dialog,
            text=f"Testing Deep Links for: {self.selected_package}",
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Instructions
        instructions = customtkinter.CTkLabel(
            dialog,
            text="Enter deep link URIs below. The Android DeepLink Observer script will monitor\n"
                 "and log all Intent.getData() calls when these links are triggered.",
            justify="center"
        )
        instructions.pack(pady=5)
        
        # Deep link input area
        input_frame = customtkinter.CTkFrame(dialog)
        input_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        input_label = customtkinter.CTkLabel(
            input_frame,
            text="Deep Link URIs (one per line):",
            font=customtkinter.CTkFont(size=12, weight="bold")
        )
        input_label.pack(pady=5)
        
        # Text area for deep links
        deeplink_text = customtkinter.CTkTextbox(input_frame, height=150)
        deeplink_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add some example deep links
        example_links = """# Example deep links - replace with actual app schemes:
myapp://user/profile?id=123
myapp://oauth?code=abc123&state=xyz
https://myapp.com/deep/link/path
myapp://settings/advanced"""
        deeplink_text.insert("1.0", example_links)
        
        # Buttons frame
        buttons_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        def start_testing():
            """Start the deep link testing process"""
            links = deeplink_text.get("1.0", "end").strip().split('\n')
            links = [link.strip() for link in links if link.strip() and not link.startswith('#')]
            
            if not links:
                messagebox.showerror("Error", "Please enter at least one deep link URI")
                return
            
            dialog.destroy()
            self.log_message(f"Starting deep link testing for {self.selected_package}...")
            threading.Thread(
                target=self._test_deep_links_thread,
                args=(links,),
                daemon=True
            ).start()
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        cancel_btn = customtkinter.CTkButton(
            buttons_frame,
            text="Cancel",
            command=cancel,
            fg_color="gray"
        )
        cancel_btn.pack(side="left", padx=5, expand=True)
        
        start_btn = customtkinter.CTkButton(
            buttons_frame,
            text="Start Testing",
            command=start_testing,
            fg_color="#FF6B35"
        )
        start_btn.pack(side="right", padx=5, expand=True)
    
    def _test_deep_links_thread(self, deep_links):
        """Thread function to test deep links"""
        self._update_button_state(True)
        try:
            # First, inject the Android DeepLink Observer script
            if "Android DeepLink Observer" not in BYPASS_SCRIPTS:
                self.log_message("✗ Android DeepLink Observer script not found")
                return
            
            script_content = BYPASS_SCRIPTS["Android DeepLink Observer"]["script"]
            self.log_message("Injecting Android DeepLink Observer script...")
            
            # Save script to temp file
            script_filename = "android_deeplink_observer.js"
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            # Start Frida in background to monitor
            self.log_message("Starting Frida monitoring in background...")
            cmd = [find_executable("frida") or "frida", "-U", "-f", self.selected_package, "-l", script_filename, "--no-pause"]
            self.log_message(f"[DEBUG] Frida command: {' '.join(cmd)}")

            # Start Frida process (in a separate group/session)
            if os.name == 'nt':
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    preexec_fn=os.setsid
                )
            self.status_label.configure(text="Testing deep links...")
            
            # Wait a moment for Frida to attach
            import time
            time.sleep(3)
            
            # Send deep link intents
            self.log_message(f"Testing {len(deep_links)} deep links...")
            for i, link in enumerate(deep_links, 1):
                if self.current_process.poll() is not None:
                    # Process was terminated
                    break
                    
                self.log_message(f"[{i}/{len(deep_links)}] Testing: {link}")
                
                # Send intent via ADB
                adb_exe = find_executable("adb")
                if not adb_exe:
                    self.log_message("✗ ADB executable not found in PATH for deep link testing.")
                    break

                result = subprocess.run([adb_exe, "-s", self.selected_device, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", link], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    self.log_message(f"✓ Intent sent successfully: {link}")
                else:
                    self.log_message(f"✗ Failed to send intent: {link}")
                    if result.stderr:
                        self.log_message(f"Error: {result.stderr.strip()}")
                
                # Wait between intents
                time.sleep(2)
            
            # Wait a bit more for Frida output
            time.sleep(2)
            
            # Terminate Frida process
            try:
                if self.current_process:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
            except:
                if self.current_process:
                    self.current_process.kill()
            
            # Read Frida output
            if self.current_process:
                stdout, stderr = self.current_process.communicate()
                
                if stdout:
                    self.log_message("Frida Script Output:")
                    # Split output by lines and log each
                    for line in stdout.strip().split('\n'):
                        if line.strip():
                            self.log_message(f"  {line}")
                
                if stderr:
                    self.log_message("Frida Errors:")
                    for line in stderr.strip().split('\n'):
                        if line.strip():
                            self.log_message(f"  [ERROR] {line}")
            
            self.log_message("✓ Deep link testing completed")
            
        except subprocess.TimeoutExpired:
            self.log_message("✗ Deep link testing timed out")
        except Exception as e:
            self.log_message(f"✗ Error during deep link testing: {str(e)}")
        finally:
            self.current_process = None
            self._update_button_state(False)
    
    def _append_log(self, message):
        """Append message to the log text widget."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def log_message(self, message):
        """Add message to log in a thread-safe way."""
        if threading.current_thread() is threading.main_thread():
            self._append_log(message)
        else:
            self.root.after(0, self._append_log, message)
    def _update_button_state(self, is_running):
        """Update button states based on execution status"""
        self.is_running = is_running
        state = "disabled" if is_running else "normal"
        
        # Disable action buttons while running
        for widget in [self.stop_btn]:
            if is_running:
                widget.configure(state="normal")
            else:
                widget.configure(state="disabled")
        
        self.status_label.configure(text="Running..." if is_running else "Ready")

    def stop_execution(self):
        """Stop the current script/APK execution"""
        if self.current_process:
            try:
                pid = self.current_process.pid
                self.log_message("⏹ Attempting to stop execution...")
                # On Windows use taskkill to terminate process tree
                if os.name == 'nt':
                    try:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], check=False, capture_output=True)
                    except Exception:
                        # fallback to terminate
                        self.current_process.terminate()
                else:
                    # On Unix kill the process group
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
                    except Exception:
                        self.current_process.terminate()

                # wait briefly for shutdown
                try:
                    self.current_process.wait(timeout=5)
                except Exception:
                    try:
                        self.current_process.kill()
                    except Exception:
                        pass

                self.log_message("✓ Execution stopped")
            except Exception as e:
                self.log_message(f"✗ Error stopping execution: {str(e)}")
            finally:
                self.current_process = None
                self._update_button_state(False)
        else:
            self.log_message("⚠️ No execution in progress")

# Create and run the application
if __name__ == "__main__":
    root = customtkinter.CTk()
    app = FridaAutomationUI(root)
    root.mainloop()
