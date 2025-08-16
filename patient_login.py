import getpass
import pymongo
import bcrypt
import os
import uuid
from otp_service import send_otp # Import our new function
from patient_info_collector import PatientInfoCollector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def generate_patient_id():
    """Generates a unique patient ID."""
    return f"PAT{uuid.uuid4().hex[:8].upper()}"

def send_patient_id_email(email, patient_id, username):
    """Sends patient ID to user's email."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get Gmail configuration from environment variables
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            print("❌ Error: SENDER_EMAIL and SENDER_PASSWORD must be set in .env file")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Your Patient Alert System - Patient ID"
        
        body = f"""
        Hello {username}!
        
        Your account has been successfully created.
        
        Your Patient ID is: {patient_id}
        
        Please keep this Patient ID safe. You may need it for future reference.
        
        Best regards,
        Patient Alert System Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        print(f"✅ Patient ID sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send Patient ID email: {e}")
        return False

class PatientAuth:
    """
    Handles all authentication logic and database interactions.
    """
    def __init__(self, connection_string, db_name="patients_db"):
        """Initializes the database connection."""
        self.client = None
        self.patients_collection = None
        self.doctors_collection = None
        
        try:
            self.client = pymongo.MongoClient(connection_string)
            db = self.client[db_name]
            
            # Use the correct collection names where your data is stored
            patients_collection_name = "patients_v2"
            doctors_collection_name = "doctor_v2"
            
            self.patients_collection = db[patients_collection_name]
            self.doctors_collection = db[doctors_collection_name]
            
            # Create unique indexes on patient_id, email, and mobile fields for patients
            try:
                self.patients_collection.create_index("patient_id", unique=True, sparse=True)
                self.patients_collection.create_index("email", unique=True, sparse=True)
                self.patients_collection.create_index("mobile", unique=True, sparse=True)
            except:
                pass  # Indexes might already exist
            
            # Create unique indexes for doctors
            try:
                self.doctors_collection.create_index("email", unique=True, sparse=True)
                self.doctors_collection.create_index("mobile", unique=True, sparse=True)
            except:
                pass  # Indexes might already exist
            
            print(f"Successfully connected to MongoDB database: '{db_name}'")
            print(f"  - Patients collection: '{patients_collection_name}'")
            print(f"  - Doctors collection: '{doctors_collection_name}'")
        except pymongo.errors.ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            exit()
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Fallback: try without unique index
            try:
                self.patients_collection = db["patients_fallback"]
                self.patients_collection.drop()
                print(f"Using fallback collection: 'patients_fallback'")
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                exit()

    def add_patient(self, username, email, mobile, plain_text_password, patient_id):
        """Hashes a password and stores the new patient with email, mobile, and patient_id."""
        try:
            hashed_password = bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())
            self.patients_collection.insert_one({
                "patient_id": patient_id,
                "username": username,
                "email": email,
                "mobile": mobile,
                "password_hash": hashed_password,
                "role": "patient"
            })
            return True
        except pymongo.errors.DuplicateKeyError as e:
            if "patient_id" in str(e):
                print(f"\nError: Patient ID '{patient_id}' already exists.")
            elif "email" in str(e):
                print(f"\nError: Email '{email}' already exists.")
            elif "mobile" in str(e):
                print(f"\nError: Mobile number '{mobile}' already exists.")
            else:
                print(f"\nError: Duplicate key error - {e}")
            return False

    def add_doctor(self, username, email, mobile, plain_text_password):
        """Hashes a password and stores the new doctor with email, mobile."""
        try:
            hashed_password = bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())
            self.doctors_collection.insert_one({
                "username": username,
                "email": email,
                "mobile": mobile,
                "password_hash": hashed_password,
                "role": "doctor"
            })
            return True
        except pymongo.errors.DuplicateKeyError as e:
            if "email" in str(e):
                print(f"\nError: Email '{email}' already exists.")
            elif "mobile" in str(e):
                print(f"\nError: Mobile number '{mobile}' already exists.")
            else:
                print(f"\nError: Duplicate key error - {e}")
            return False

    def login_patient(self, login_identifier, plain_text_password):
        """Authenticates a patient by Patient ID/email and password."""
        # Try to find user by Patient ID first, then by email
        patient_document = self.patients_collection.find_one({"patient_id": login_identifier})
        if not patient_document:
            # If not found by Patient ID, try by email
            patient_document = self.patients_collection.find_one({"email": login_identifier})
        
        if patient_document:
            stored_hash = patient_document["password_hash"]
            if bcrypt.checkpw(plain_text_password.encode('utf-8'), stored_hash):
                return True, patient_document
        return False, None

    def login_doctor(self, login_identifier, plain_text_password):
        """Authenticates a doctor by email."""
        # Try to find doctor by email
        doctor_document = self.doctors_collection.find_one({"email": login_identifier})
        
        if doctor_document:
            stored_hash = doctor_document["password_hash"]
            if bcrypt.checkpw(plain_text_password.encode('utf-8'), stored_hash):
                return True, doctor_document
        return False, None

    def login_user(self, login_identifier, plain_text_password, role):
        """Authenticates a user by role (patient or doctor)."""
        if role == "doctor":
            return self.login_doctor(login_identifier, plain_text_password)
        else:
            return self.login_patient(login_identifier, plain_text_password)

    def does_user_exist(self, username):
        """Checks if a user exists in the database by username."""
        # Check both patients and doctors collections
        patient_exists = self.patients_collection.count_documents({"username": username}) > 0
        doctor_exists = self.doctors_collection.count_documents({"username": username}) > 0
        return patient_exists or doctor_exists

    def does_email_exist(self, email):
        """Checks if an email already exists in the database."""
        # Check both patients and doctors collections
        patient_exists = self.patients_collection.count_documents({"email": email}) > 0
        doctor_exists = self.doctors_collection.count_documents({"email": email}) > 0
        return patient_exists or doctor_exists

    def does_mobile_exist(self, mobile):
        """Checks if a mobile number already exists in the database."""
        # Check both patients and doctors collections
        patient_exists = self.patients_collection.count_documents({"mobile": mobile}) > 0
        doctor_exists = self.doctors_collection.count_documents({"mobile": mobile}) > 0
        return patient_exists or doctor_exists

    def does_patient_id_exist(self, patient_id):
        """Checks if a Patient ID already exists in the database."""
        return self.patients_collection.count_documents({"patient_id": patient_id}) > 0

    def update_password(self, username, new_password):
        """Updates the password for a user."""
        try:
            new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Try to update in patients collection first
            result = self.patients_collection.update_one(
                {"username": username},
                {"$set": {"password_hash": new_hashed_password}}
            )
            
            # If not found in patients, try doctors collection
            if result.modified_count == 0:
                result = self.doctors_collection.update_one(
                    {"username": username},
                    {"$set": {"password_hash": new_hashed_password}}
                )
            
            if result.modified_count > 0:
                return True
            else:
                print(f"User '{username}' not found in either collection")
                return False
                
        except Exception as e:
            print(f"Error updating password: {e}")
            return False

    def close_connection(self):
        """Closes the database connection."""
        if self.client:
            self.client.close()
            print("\nDatabase connection closed.")


class CommandLineUI:
    """
    Handles all command-line user interface interactions.
    """
    def __init__(self, auth_system):
        self.auth = auth_system

    def run_signup(self):
        """Handles the user registration process with OTP verification."""
        print("\n--- Create a New Account ---")
        print("1: Patient Account")
        print("2: Doctor Account")
        role_choice = input("Please choose account type: ")
        
        if role_choice not in ['1', '2']:
            print("\nInvalid choice. Please select 1 for Patient or 2 for Doctor.")
            return
        
        role = "patient" if role_choice == '1' else "doctor"
        account_type = "Patient" if role == "patient" else "Doctor"
        
        print(f"\n--- Create a New {account_type} Account ---")
        username = input("Enter your username: ")
        email = input("Enter your email address: ")
        mobile = input("Enter your mobile number: ")
        password = getpass.getpass("Enter a password: ")
        password_confirm = getpass.getpass("Confirm your password: ")

        if not username or not password or not email or not mobile:
            print("\nUsername, email, mobile, and password cannot be empty.")
            return

        if password != password_confirm:
            print("\nPasswords do not match. Please try again.")
            return
        
        # Check if username already exists
        if self.auth.does_user_exist(username):
            print(f"\nAn account with the username '{username}' already exists.")
            return

        # Check if email already exists
        if self.auth.does_email_exist(email):
            print(f"\nAn account with the email '{email}' already exists.")
            return

        # Check if mobile number already exists
        if self.auth.does_mobile_exist(mobile):
            print(f"\nAn account with the mobile number '{mobile}' already exists.")
            return

        # --- OTP Verification Flow ---
        print(f"\nSending OTP verification to: {email}")
        generated_otp = send_otp(email)
        if generated_otp is None:
            return # Stop if email failed to send

        user_otp = input("Please enter the OTP you received via email: ")

        if user_otp == generated_otp:
            print("\nOTP verified successfully!")
            
            if role == "patient":
                patient_id = generate_patient_id()
                print(f"\n🎉 Patient Account created successfully!")
                print(f"📋 Your Patient ID: {patient_id}")
                print(f"👤 Username: {username}")
                print(f"📧 Email: {email}")
                print(f"📱 Mobile: {mobile}")
                
                # Send patient ID to email
                if send_patient_id_email(email, patient_id, username):
                    if self.auth.add_patient(username, email, mobile, password, patient_id):
                        print(f"\n✅ Patient ID has been sent to your email: {email}")
                        print(f"📧 Please check your email for your Patient ID")
                    else:
                        print(f"\n❌ Failed to save account to database")
                else:
                    print(f"\n⚠️  Account created but failed to send Patient ID email")
                    if self.auth.add_patient(username, email, mobile, password, patient_id):
                        print(f"✅ Account saved successfully")
            else:
                # Doctor account
                print(f"\n🎉 Doctor Account created successfully!")
                print(f"👤 Username: {username}")
                print(f"📧 Email: {email}")
                print(f"📱 Mobile: {mobile}")
                
                if self.auth.add_doctor(username, email, mobile, password):
                    print(f"\n✅ Doctor account saved successfully!")
                    print(f"📧 Please check your email for further instructions")
                else:
                    print(f"\n❌ Failed to save doctor account to database")
        else:
            print("\nInvalid OTP. Signup failed.")

    def run_login(self):
        """Handles the user login process and returns True on success."""
        print("\n--- User Login ---")
        print("1: Patient Login")
        print("2: Doctor Login")
        role_choice = input("Please choose login type: ")
        
        if role_choice not in ['1', '2']:
            print("\nInvalid choice. Please select 1 for Patient or 2 for Doctor.")
            return False
        
        role = "patient" if role_choice == '1' else "doctor"
        login_type = "Patient" if role == "patient" else "Doctor"
        
        print(f"\n--- {login_type} Portal Login ---")
        if role == "patient":
            login_identifier = input("Enter your Patient ID or Email: ")
        else:
            login_identifier = input("Enter your Email: ")
        
        password = getpass.getpass("Enter your password: ")

        if role == "patient":
            login_successful, user_doc = self.auth.login_patient(login_identifier, password)
        else:
            login_successful, user_doc = self.auth.login_doctor(login_identifier, password)

        if login_successful:
            print(f"\nLogin successful! Welcome, {user_doc['username']}.")
            
            if role == "patient":
                # Check if patient has completed their profile
                if not self.is_profile_complete(user_doc):
                    print("\n📋 Profile Incomplete - Information Collection Required")
                    print("Please complete your profile information to continue.")
                    
                    # Initialize patient info collector
                    info_collector = PatientInfoCollector(self.auth)
                    
                    # Collect patient information
                    if info_collector.collect_all_info(user_doc):
                        print("\n✅ Profile completed successfully!")
                    else:
                        print("\n❌ Failed to complete profile. Please try again later.")
                        return False
                else:
                    print("\n✅ Profile already completed!")
                    self.show_welcome_message(user_doc)
            else:
                # Doctor login
                print(f"\n👨‍⚕️ Welcome, Dr. {user_doc['username']}!")
                print("Your account is ready. Please complete your professional profile.")
                print("You can access the Flutter app to complete your profile.")
            
            return True
        else:
            if role == "patient":
                print("\nLogin failed. Please check your Patient ID/Email and password.")
            else:
                print("\nLogin failed. Please check your Email and password.")
            return False

    def run_forgot_password(self):
        """Handles the forgot password workflow with OTP verification."""
        print("\n--- Forgot Password ---")
        login_identifier = input("Enter your Patient ID or Email to reset your password: ")
        
        if not login_identifier:
            print("\nPatient ID or Email cannot be empty.")
            return
        
        # Find user by Patient ID or email in both collections
        user_doc = self.auth.patients_collection.find_one({"patient_id": login_identifier})
        if not user_doc:
            user_doc = self.auth.patients_collection.find_one({"email": login_identifier})
        if not user_doc:
            user_doc = self.auth.doctors_collection.find_one({"email": login_identifier})
        
        if user_doc:
            email = user_doc.get("email", "")
            username = user_doc.get("username", "")
            if email:
                print(f"\nSending OTP verification to: {email}")
                generated_otp = send_otp(email)
                if generated_otp is None:
                    return # Stop if email failed to send

                user_otp = input("Please enter the OTP you received via email: ")

                if user_otp == generated_otp:
                    print("\nOTP verified successfully!")
                    # Allow user to set new password
                    new_password = getpass.getpass("Enter your new password: ")
                    new_password_confirm = getpass.getpass("Confirm your new password: ")
                    
                    if new_password != new_password_confirm:
                        print("\nPasswords do not match. Password reset failed.")
                        return
                    
                    if self.auth.update_password(username, new_password):
                        print(f"\nPassword for '{username}' has been reset successfully!")
                    else:
                        print("\nPassword reset failed. Please try again.")
                else:
                    print("\nInvalid OTP. Password reset failed.")
            else:
                print("\nNo email address found for this user.")
        else:
            print("\nNo account found with that Patient ID or Email.")

    def start(self):
        """Starts the main application loop."""
        while True:
                    print("\n=====================================")
        print(" Welcome to the Patient & Doctor Alert System")
        print("=====================================")
        print("1: Login")
        print("2: Signup")
        print("3: Forgot Password")
        print("4: Exit")
            choice = input("Please choose an option: ")

            if choice == '1':
                if self.run_login():
                    break
            elif choice == '2':
                self.run_signup()
            elif choice == '3':
                self.run_forgot_password()
            elif choice == '4':
                break
            else:
                print("\nInvalid option, please try again.")
        
        print("\nThank you for using the system.")
    
    def is_profile_complete(self, patient_doc):
        """Check if patient has completed their profile information."""
        # Check if basic profile information exists
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'blood_type']
        return all(field in patient_doc for field in required_fields)
    
    def show_welcome_message(self, patient_doc):
        """Display welcome message with patient information."""
        print("\n" + "="*60)
        print("🎉 WELCOME BACK!")
        print("="*60)
        
        first_name = patient_doc.get('first_name', '')
        last_name = patient_doc.get('last_name', '')
        age = patient_doc.get('age', '')
        blood_type = patient_doc.get('blood_type', '')
        
        if first_name and last_name:
            print(f"👤 Name: {first_name} {last_name}")
        if age:
            print(f"📅 Age: {age} years")
        if blood_type:
            print(f"🩸 Blood Type: {blood_type}")
        
        # Show pregnancy information if applicable
        if patient_doc.get('is_pregnant'):
            pregnancy_week = patient_doc.get('pregnancy_week', '')
            expected_delivery = patient_doc.get('expected_delivery_date', '')
            print(f"🤱 Pregnancy Week: {pregnancy_week}")
            if expected_delivery:
                print(f"📅 Expected Delivery: {expected_delivery}")
        
        print("✅ Your profile is complete and up to date!")
        print("="*60)


if __name__ == "__main__":
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "patients_db")
    
    auth_system = PatientAuth(MONGO_URI, DB_NAME)
    ui = CommandLineUI(auth_system)
    ui.start() 