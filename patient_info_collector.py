import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class PatientInfoCollector:
    """
    Handles collection and management of detailed patient information.
    """
    
    def __init__(self, auth_system):
        self.auth = auth_system
    
    def calculate_age(self, date_of_birth):
        """Calculate age from date of birth."""
        today = date.today()
        age = relativedelta(today, date_of_birth).years
        return age
    
    def validate_date_of_birth(self, dob):
        """Validate date of birth and return appropriate message."""
        today = date.today()
        
        if dob > today:
            return False, "❌ Date of birth cannot be in the future!"
        
        age = self.calculate_age(dob)
        if age > 120:
            return False, "❌ Please enter a valid date of birth (age cannot exceed 120 years)"
        
        if age < 0:
            return False, "❌ Please enter a valid date of birth"
        
        return True, f"Age: {age} years"
    
    def calculate_pregnancy_week(self, last_menstrual_period):
        """Calculate current pregnancy week from LMP."""
        if not last_menstrual_period:
            return None
        
        today = date.today()
        weeks_pregnant = (today - last_menstrual_period).days // 7
        return max(1, min(42, weeks_pregnant))
    
    def collect_basic_info(self, patient_doc):
        """Collect basic patient information."""
        print("\n" + "="*60)
        print("📋 PATIENT INFORMATION COLLECTION")
        print("="*60)
        
        # Get existing data
        patient_id = patient_doc.get("patient_id", "")
        username = patient_doc.get("username", "")
        email = patient_doc.get("email", "")
        mobile = patient_doc.get("mobile", "")
        
        print(f"Patient ID: {patient_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Mobile: {mobile}")
        print("="*60)
        
        # Collect new information
        print("\n--- Personal Information ---")
        first_name = input("Enter your first name: ").strip()
        last_name = input("Enter your last name: ").strip()
        
        # Date of birth
        while True:
            try:
                dob_str = input("Enter your date of birth (YYYY-MM-DD): ").strip()
                date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
                is_valid, age_message = self.validate_date_of_birth(date_of_birth)
                if is_valid:
                    print(age_message)
                    break
                else:
                    print(age_message)
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD")
        
        # Physical information
        print("\n--- Physical Information ---")
        blood_type = input("Enter your blood type (e.g., A+, B-, O+): ").strip().upper()
        
        height_input = input("Enter your height in cm: ").strip()
        height_cm = float(height_input) if height_input else None
        
        weight_input = input("Enter your pre-pregnancy weight in kg: ").strip()
        pre_pregnancy_weight_kg = float(weight_input) if weight_input else None
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "age": self.calculate_age(date_of_birth),
            "blood_type": blood_type,
            "height_cm": height_cm,
            "pre_pregnancy_weight_kg": pre_pregnancy_weight_kg
        }
    
    def collect_pregnancy_info(self):
        """Collect pregnancy-specific information."""
        print("\n--- Pregnancy Information ---")
        
        # Pregnancy status
        is_pregnant = input("Are you currently pregnant? (y/n): ").strip().lower() == 'y'
        
        pregnancy_data = {
            "is_pregnant": is_pregnant,
            "pregnancy_week": None,
            "expected_delivery_date": None,
            "last_menstrual_period": None
        }
        
        if is_pregnant:
            # LMP date
            while True:
                try:
                    lmp_str = input("Enter your last menstrual period date (YYYY-MM-DD): ").strip()
                    last_menstrual_period = datetime.strptime(lmp_str, "%Y-%m-%d").date()
                    pregnancy_data["last_menstrual_period"] = last_menstrual_period
                    
                    # Calculate pregnancy week
                    pregnancy_week = self.calculate_pregnancy_week(last_menstrual_period)
                    pregnancy_data["pregnancy_week"] = pregnancy_week
                    print(f"Current pregnancy week: {pregnancy_week}")
                    
                    # Calculate expected delivery date (40 weeks from LMP)
                    expected_delivery_date = last_menstrual_period + relativedelta(weeks=40)
                    pregnancy_data["expected_delivery_date"] = expected_delivery_date
                    print(f"Expected delivery date: {expected_delivery_date}")
                    break
                except ValueError:
                    print("❌ Invalid date format. Please use YYYY-MM-DD")
            
            # Pregnancy details
            print("\n--- Pregnancy Details ---")
            pregnancy_number = input("Is this your 1st, 2nd, 3rd pregnancy? Enter number: ").strip()
            pregnancy_data["pregnancy_number"] = int(pregnancy_number) if pregnancy_number.isdigit() else 1
            
            delivery_method = input("Planned delivery method (vaginal/caesarean): ").strip().lower()
            pregnancy_data["delivery_method"] = delivery_method
            
            # Notes
            notes = input("Additional pregnancy notes: ").strip()
            pregnancy_data["notes"] = notes
        
        return pregnancy_data
    
    def collect_emergency_contact(self):
        """Collect emergency contact information."""
        print("\n--- Emergency Contact Information ---")
        
        emergency_contact = {}
        
        name = input("Emergency contact name: ").strip()
        if name:
            emergency_contact["name"] = name
            
            relationship = input("Relationship to you: ").strip()
            if relationship:
                emergency_contact["relationship"] = relationship
            
            phone = input("Emergency contact phone: ").strip()
            if phone:
                emergency_contact["phone"] = phone
            
            email = input("Emergency contact email: ").strip()
            if email:
                emergency_contact["email"] = email
        
        return emergency_contact
    
    def collect_preferences(self):
        """Collect user preferences."""
        print("\n--- User Preferences ---")
        
        preferences = {}
        
        # Communication preferences
        print("Communication preferences:")
        email_notifications = input("Receive email notifications? (y/n): ").strip().lower() == 'y'
        sms_notifications = input("Receive SMS notifications? (y/n): ").strip().lower() == 'y'
        
        preferences["notifications"] = {
            "email": email_notifications,
            "sms": sms_notifications
        }
        
        # Language preference
        language = input("Preferred language (English/Hindi/Tamil): ").strip()
        if language:
            preferences["language"] = language
        
        # Reminder preferences
        reminder_frequency = input("Reminder frequency (daily/weekly/monthly): ").strip()
        if reminder_frequency:
            preferences["reminder_frequency"] = reminder_frequency
        
        return preferences
    
    def save_patient_info(self, patient_doc, basic_info, pregnancy_info, emergency_contact, preferences):
        """Save all collected information to database."""
        try:
            # Convert date objects to string format for MongoDB storage
            basic_info_copy = basic_info.copy()
            if 'date_of_birth' in basic_info_copy:
                basic_info_copy['date_of_birth'] = basic_info_copy['date_of_birth'].isoformat()
            
            # Prepare update data
            update_data = {
                **basic_info_copy,
                "emergency_contact": emergency_contact,
                "preferences": preferences,
                "status": "active",
                "updated_at": datetime.now()
            }
            
            # Add pregnancy info if pregnant
            if pregnancy_info.get("is_pregnant"):
                pregnancy_data = {
                    "pregnancy_week": pregnancy_info["pregnancy_week"],
                    "expected_delivery_date": pregnancy_info["expected_delivery_date"].isoformat() if pregnancy_info["expected_delivery_date"] else None,
                    "is_pregnant": True
                }
                update_data.update(pregnancy_data)
            
            # Update the patient document
            self.auth.patients_collection.update_one(
                {"_id": patient_doc["_id"]},
                {"$set": update_data}
            )
            
            print("\n✅ Patient information saved successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error saving patient information: {e}")
            return False
    
    def collect_all_info(self, patient_doc):
        """Main function to collect all patient information."""
        print("\n🎉 Welcome to Patient Information Collection!")
        print("Please provide the following information to complete your profile.")
        
        # Collect basic information
        basic_info = self.collect_basic_info(patient_doc)
        
        # Collect pregnancy information
        pregnancy_info = self.collect_pregnancy_info()
        
        # Collect emergency contact
        emergency_contact = self.collect_emergency_contact()
        
        # Collect preferences
        preferences = self.collect_preferences()
        
        # Save all information
        success = self.save_patient_info(patient_doc, basic_info, pregnancy_info, emergency_contact, preferences)
        
        if success:
            print("\n" + "="*60)
            print("📋 PROFILE COMPLETION SUMMARY")
            print("="*60)
            print(f"Name: {basic_info['first_name']} {basic_info['last_name']}")
            print(f"Age: {basic_info['age']} years")
            print(f"Blood Type: {basic_info['blood_type']}")
            
            if pregnancy_info.get("is_pregnant"):
                print(f"Pregnancy Week: {pregnancy_info['pregnancy_week']}")
                print(f"Expected Delivery: {pregnancy_info['expected_delivery_date']}")
            
            print("✅ Your profile has been completed successfully!")
            print("="*60)
        
        return success 