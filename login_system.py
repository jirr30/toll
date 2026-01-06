#!/data/data/com.termux/files/usr/bin/python3
"""
LOGIN SYSTEM FOR TERMUX
Structured and Modular Python Application
Author: Termux Developer
"""

import os
import sys
import time
import json
import hashlib
import getpass
from datetime import datetime

# ======================
# CONFIGURATION SECTION
# ======================
class Config:
    """Konfigurasi aplikasi"""
    DB_FILE = "users.json"
    LOG_FILE = "access.log"
    MAX_ATTEMPTS = 3
    SESSION_TIMEOUT = 300  # 5 menit dalam detik
    
    # Warna terminal (ANSI codes)
    COLORS = {
        'RESET': '\033[0m',
        'RED': '\033[1;31m',
        'GREEN': '\033[1;32m',
        'YELLOW': '\033[1;33m',
        'BLUE': '\033[1;34m',
        'MAGENTA': '\033[1;35m',
        'CYAN': '\033[1;36m',
        'WHITE': '\033[1;37m'
    }

# ======================
# DATABASE MANAGER
# ======================
class DatabaseManager:
    """Mengelola penyimpanan data pengguna"""
    
    @staticmethod
    def load_users():
        """Memuat data pengguna dari file JSON"""
        if os.path.exists(Config.DB_FILE):
            try:
                with open(Config.DB_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        # Data default jika file tidak ada
        return {
            "admin": {
                "password": DatabaseManager.hash_password("admin123"),
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "admin"
            }
        }
    
    @staticmethod
    def save_users(users_data):
        """Menyimpan data pengguna ke file JSON"""
        with open(Config.DB_FILE, 'w') as f:
            json.dump(users_data, f, indent=4, sort_keys=True)
    
    @staticmethod
    def hash_password(password):
        """Hash password menggunakan SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user(username, password, level="user"):
        """Membuat pengguna baru"""
        users = DatabaseManager.load_users()
        
        if username in users:
            return False, "Username sudah terdaftar"
        
        users[username] = {
            "password": DatabaseManager.hash_password(password),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "last_login": None
        }
        
        DatabaseManager.save_users(users)
        return True, "User berhasil dibuat"
    
    @staticmethod
    def update_last_login(username):
        """Update waktu login terakhir"""
        users = DatabaseManager.load_users()
        if username in users:
            users[username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            DatabaseManager.save_users(users)

# ======================
# LOGGER CLASS
# ======================
class Logger:
    """Mencatat aktivitas sistem"""
    
    @staticmethod
    def log_event(event_type, username, status, details=""):
        """Mencatat event ke log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type.upper()} | User: {username} | Status: {status} | {details}\n"
        
        with open(Config.LOG_FILE, 'a') as f:
            f.write(log_entry)
    
    @staticmethod
    def show_logs(limit=10):
        """Menampilkan log terakhir"""
        if not os.path.exists(Config.LOG_FILE):
            return "Log file tidak ditemukan"
        
        with open(Config.LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        return "".join(lines[-limit:])

# ======================
# UI HELPER CLASS
# ======================
class UIHelper:
    """Helper untuk tampilan antarmuka"""
    
    @staticmethod
    def clear_screen():
        """Membersihkan layar terminal"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    @staticmethod
    def print_color(text, color):
        """Mencetak teks dengan warna"""
        color_code = Config.COLORS.get(color.upper(), Config.COLORS['RESET'])
        print(f"{color_code}{text}{Config.COLORS['RESET']}")
    
    @staticmethod
    def print_header(title):
        """Mencetak header yang terstruktur"""
        UIHelper.clear_screen()
        print("=" * 50)
        UIHelper.print_color(f"    {title}", "CYAN")
        print("=" * 50)
    
    @staticmethod
    def print_menu(title, options):
        """Menampilkan menu dengan pilihan"""
        UIHelper.print_header(title)
        for i, (key, desc) in enumerate(options.items(), 1):
            print(f"  {i}. {desc}")
        print("=" * 50)
    
    @staticmethod
    def get_input(prompt, password=False):
        """Mendapatkan input dari pengguna"""
        if password:
            return getpass.getpass(prompt)
        return input(prompt).strip()
    
    @staticmethod
    def loading_animation(text="Loading", duration=1):
        """Animasi loading sederhana"""
        for i in range(3):
            sys.stdout.write(f"\r{text}{'.' * (i+1)}")
            sys.stdout.flush()
            time.sleep(0.3)
        print()

# ======================
# AUTHENTICATION CLASS
# ======================
class Authentication:
    """Mengelola proses autentikasi"""
    
    def __init__(self):
        self.users = DatabaseManager.load_users()
        self.attempts = {}
    
    def login(self):
        """Proses login utama"""
        UIHelper.print_header("LOGIN SYSTEM")
        
        # Reset attempts jika sudah timeout
        self._cleanup_attempts()
        
        username = UIHelper.get_input("Username: ")
        
        # Cek apakah user dikunci
        if self._is_user_locked(username):
            UIHelper.print_color("Akun terkunci! Coba lagi nanti.", "RED")
            time.sleep(2)
            return None
        
        password = UIHelper.get_input("Password: ", password=True)
        
        # Verifikasi login
        user = self._verify_credentials(username, password)
        
        if user:
            self.attempts.pop(username, None)  # Reset attempts
            DatabaseManager.update_last_login(username)
            Logger.log_event("LOGIN", username, "SUCCESS")
            UIHelper.print_color("\nLogin berhasil!", "GREEN")
            time.sleep(1)
            return username
        else:
            # Hitung attempts
            current_attempts = self.attempts.get(username, 0) + 1
            self.attempts[username] = current_attempts
            remaining = Config.MAX_ATTEMPTS - current_attempts
            
            Logger.log_event("LOGIN", username, "FAILED", f"Attempt {current_attempts}")
            UIHelper.print_color(f"\nLogin gagal! Sisa percobaan: {remaining}", "RED")
            time.sleep(2)
            return None
    
    def _verify_credentials(self, username, password):
        """Memverifikasi username dan password"""
        if username in self.users:
            stored_hash = self.users[username]["password"]
            input_hash = DatabaseManager.hash_password(password)
            return stored_hash == input_hash
        return False
    
    def _is_user_locked(self, username):
        """Cek apakah user dikunci karena terlalu banyak attempt"""
        if username in self.attempts:
            return self.attempts[username] >= Config.MAX_ATTEMPTS
        return False
    
    def _cleanup_attempts(self):
        """Bersihkan attempt records yang sudah lama"""
        # Implementasi sederhana
        pass

# ======================
# MENU SYSTEM
# ======================
class MenuSystem:
    """Sistem menu aplikasi"""
    
    def __init__(self, username):
        self.username = username
        self.users = DatabaseManager.load_users()
        self.user_level = self.users.get(username, {}).get("level", "user")
    
    def main_menu(self):
        """Menu utama aplikasi"""
        while True:
            options = {
                1: "System Information",
                2: "File Operations",
                3: "Network Tools",
                4: "Package Manager",
                5: "User Management" if self.user_level == "admin" else "Change Password",
                6: "View Logs" if self.user_level == "admin" else "About",
                0: "Logout"
            }
            
            UIHelper.print_menu("MAIN MENU", options)
            
            try:
                choice = int(UIHelper.get_input("Pilih menu [0-6]: "))
            except ValueError:
                UIHelper.print_color("Input tidak valid!", "RED")
                time.sleep(1)
                continue
            
            if choice == 0:
                self.logout()
                break
            elif choice == 1:
                self.system_info()
            elif choice == 2:
                self.file_operations()
            elif choice == 3:
                self.network_tools()
            elif choice == 4:
                self.package_manager()
            elif choice == 5:
                if self.user_level == "admin":
                    self.user_management()
                else:
                    self.change_password()
            elif choice == 6:
                if self.user_level == "admin":
                    self.view_logs()
                else:
                    self.about()
            else:
                UIHelper.print_color("Pilihan tidak tersedia!", "YELLOW")
                time.sleep(1)
    
    def system_info(self):
        """Menu informasi sistem"""
        UIHelper.print_header("SYSTEM INFORMATION")
        
        info_options = {
            1: "Show OS Info",
            2: "Show Disk Usage",
            3: "Show Memory Info",
            4: "Show Process List",
            5: "Back"
        }
        
        while True:
            UIHelper.print_menu("System Info", info_options)
            
            try:
                choice = int(UIHelper.get_input("Pilih [1-5]: "))
            except ValueError:
                continue
            
            if choice == 1:
                os.system('uname -a')
            elif choice == 2:
                os.system('df -h')
            elif choice == 3:
                os.system('free -m')
            elif choice == 4:
                os.system('ps aux | head -20')
            elif choice == 5:
                break
            
            input("\nTekan Enter untuk lanjut...")
    
    def file_operations(self):
        """Operasi file"""
        UIHelper.print_header("FILE OPERATIONS")
        
        file_ops = {
            1: "List Files",
            2: "Create Directory",
            3: "Delete File",
            4: "View File",
            5: "Back"
        }
        
        while True:
            UIHelper.print_menu("File Operations", file_ops)
            
            try:
                choice = int(UIHelper.get_input("Pilih [1-5]: "))
            except ValueError:
                continue
            
            if choice == 1:
                os.system('ls -la')
            elif choice == 2:
                dir_name = UIHelper.get_input("Nama direktori: ")
                os.system(f'mkdir {dir_name}')
            elif choice == 3:
                file_name = UIHelper.get_input("Nama file: ")
                os.system(f'rm -i {file_name}')
            elif choice == 4:
                file_name = UIHelper.get_input("Nama file: ")
                os.system(f'cat {file_name}')
            elif choice == 5:
                break
            
            input("\nTekan Enter...")
    
    def network_tools(self):
        """Tools jaringan"""
        UIHelper.print_header("NETWORK TOOLS")
        
        # Implementasi network tools
        print("1. Check IP Address")
        print("2. Ping Test")
        print("3. Back")
        
        choice = UIHelper.get_input("Pilih [1-3]: ")
        
        if choice == "1":
            os.system('ifconfig | grep "inet "')
        elif choice == "2":
            host = UIHelper.get_input("Host/URL: ")
            os.system(f'ping -c 4 {host}')
        
        input("\nTekan Enter...")
    
    def package_manager(self):
        """Manajer paket"""
        UIHelper.print_header("PACKAGE MANAGER")
        
        print("1. Install Package")
        print("2. Update System")
        print("3. Back")
        
        choice = UIHelper.get_input("Pilih [1-3]: ")
        
        if choice == "1":
            pkg = UIHelper.get_input("Nama package: ")
            os.system(f'pkg install {pkg}')
        elif choice == "2":
            os.system('pkg update && pkg upgrade')
        
        input("\nTekan Enter...")
    
    def user_management(self):
        """Manajemen user (admin only)"""
        UIHelper.print_header("USER MANAGEMENT")
        
        user_ops = {
            1: "Create User",
            2: "List Users",
            3: "Delete User",
            4: "Back"
        }
        
        while True:
            UIHelper.print_menu("User Management", user_ops)
            
            try:
                choice = int(UIHelper.get_input("Pilih [1-4]: "))
            except ValueError:
                continue
            
            if choice == 1:
                self.create_user()
            elif choice == 2:
                self.list_users()
            elif choice == 3:
                self.delete_user()
            elif choice == 4:
                break
    
    def create_user(self):
        """Membuat user baru"""
        username = UIHelper.get_input("Username baru: ")
        password = UIHelper.get_input("Password: ", password=True)
        confirm = UIHelper.get_input("Konfirmasi password: ", password=True)
        
        if password != confirm:
            UIHelper.print_color("Password tidak cocok!", "RED")
            time.sleep(1)
            return
        
        success, message = DatabaseManager.create_user(username, password)
        UIHelper.print_color(message, "GREEN" if success else "RED")
        time.sleep(1)
    
    def list_users(self):
        """Menampilkan daftar user"""
        users = DatabaseManager.load_users()
        
        print("\n" + "=" * 60)
        print(f"{'USERNAME':<20} {'LEVEL':<10} {'CREATED':<20}")
        print("=" * 60)
        
        for username, data in users.items():
            print(f"{username:<20} {data.get('level','user'):<10} {data.get('created',''):<20}")
        
        input("\nTekan Enter...")
    
    def delete_user(self):
        """Menghapus user"""
        username = UIHelper.get_input("Username yang akan dihapus: ")
        
        if username == self.username:
            UIHelper.print_color("Tidak bisa menghapus diri sendiri!", "RED")
            time.sleep(1)
            return
        
        users = DatabaseManager.load_users()
        
        if username in users:
            del users[username]
            DatabaseManager.save_users(users)
            UIHelper.print_color(f"User {username} berhasil dihapus", "GREEN")
        else:
            UIHelper.print_color("User tidak ditemukan!", "RED")
        
        time.sleep(1)
    
    def change_password(self):
        """Mengubah password user"""
        UIHelper.print_header("CHANGE PASSWORD")
        
        old_pass = UIHelper.get_input("Password lama: ", password=True)
        new_pass = UIHelper.get_input("Password baru: ", password=True)
        confirm = UIHelper.get_input("Konfirmasi password: ", password=True)
        
        users = DatabaseManager.load_users()
        
        if DatabaseManager.hash_password(old_pass) != users[self.username]["password"]:
            UIHelper.print_color("Password lama salah!", "RED")
            time.sleep(2)
            return
        
        if new_pass != confirm:
            UIHelper.print_color("Password baru tidak cocok!", "RED")
            time.sleep(2)
            return
        
        users[self.username]["password"] = DatabaseManager.hash_password(new_pass)
        DatabaseManager.save_users(users)
        
        UIHelper.print_color("Password berhasil diubah!", "GREEN")
        time.sleep(2)
    
    def view_logs(self):
        """Menampilkan log"""
        UIHelper.print_header("SYSTEM LOGS")
        print(Logger.show_logs(20))
        input("\nTekan Enter...")
    
    def about(self):
        """Tentang aplikasi"""
        UIHelper.print_header("ABOUT")
        print("Termux Login System v1.0")
        print("Structured Python Application")
        print("Author: Developer")
        print("\nFeatures:")
        print("- User Authentication")
        print("- Menu System")
        print("- File Operations")
        print("- System Tools")
        input("\nTekan Enter...")
    
    def logout(self):
        """Proses logout"""
        Logger.log_event("LOGOUT", self.username, "SUCCESS")
        UIHelper.print_color("Logout berhasil!", "GREEN")
        time.sleep(1)

# ======================
# MAIN APPLICATION
# ======================
class TermuxApp:
    """Aplikasi utama Termux"""
    
    def __init__(self):
        self.auth = Authentication()
    
    def run(self):
        """Menjalankan aplikasi"""
        UIHelper.loading_animation("Starting System")
        
        # Login loop
        while True:
            username = self.auth.login()
            
            if username:
                # Inisialisasi menu system
                menu_system = MenuSystem(username)
                menu_system.main_menu()
            else:
                retry = UIHelper.get_input("\nCoba lagi? (y/n): ").lower()
                if retry != 'y':
                    UIHelper.print_color("\nProgram dihentikan", "YELLOW")
                    break
    
    @staticmethod
    def init_system():
        """Inisialisasi sistem"""
        # Pastikan file database ada
        if not os.path.exists(Config.DB_FILE):
            DatabaseManager.save_users(DatabaseManager.load_users())
            UIHelper.print_color("Database initialized", "GREEN")

# ======================
# ENTRY POINT
# ======================
if __name__ == "__main__":
    try:
        # Inisialisasi sistem
        TermuxApp.init_system()
        
        # Jalankan aplikasi
        app = TermuxApp()
        app.run()
        
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user")
        sys.exit(0)
    except Exception as e:
        UIHelper.print_color(f"Error: {str(e)}", "RED")
        sys.exit(1)
