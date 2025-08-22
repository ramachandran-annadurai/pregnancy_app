#!/usr/bin/env python3
"""
Clean up duplicate nutrition endpoints in app_simple.py
"""

def clean_app_simple():
    """Remove duplicate nutrition endpoints from app_simple.py"""
    
    input_file = 'app_simple.py'
    output_file = 'app_simple_clean.py'
    
    print("🧹 Cleaning up duplicate nutrition endpoints...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 Original file has {len(lines)} lines")
    
    # Find the start and end of old nutrition section (around line 4363-5045)
    old_nutrition_start = None
    old_nutrition_end = None
    
    # We know the exact boundaries from manual inspection
    for i, line in enumerate(lines):
        if 'def get_pregnancy_info(patient_id):' in line:
            old_nutrition_start = i
            print(f"🔍 Found old nutrition section start at line {i+1}")
            break
    
    # Look for the end boundary
    for i in range(old_nutrition_start + 1, len(lines)):
        if '@app.route.*get-patient-profile-by-email' in lines[i]:
            old_nutrition_end = i
            print(f"🔍 Found old nutrition section end at line {i+1}")
            break
    
    # If we still can't find it, use the known boundaries
    if old_nutrition_start is None or old_nutrition_end is None:
        print("🔍 Using known boundaries...")
        old_nutrition_start = 4362  # Line 4363 (0-indexed)
        old_nutrition_end = 5045     # Line 5046 (0-indexed)
        print(f"🔍 Using known boundaries: lines {old_nutrition_start+1} to {old_nutrition_end+1}")
    
    if old_nutrition_start is not None and old_nutrition_end is not None:
        print(f"✂️ Removing lines {old_nutrition_start+1} to {old_nutrition_end+1}")
        
        # Remove the old nutrition section
        cleaned_lines = lines[:old_nutrition_start] + lines[old_nutrition_end:]
        
        print(f"📄 Cleaned file has {len(cleaned_lines)} lines")
        print(f"🗑️ Removed {old_nutrition_end - old_nutrition_start} lines")
        
        # Write cleaned file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        
        print(f"✅ Cleaned file saved as: {output_file}")
        
        # Backup original
        backup_file = 'app_simple_backup.py'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"💾 Original file backed up as: {backup_file}")
        
    else:
        print("❌ Could not find old nutrition section boundaries")
        return False
    
    return True

if __name__ == "__main__":
    try:
        if clean_app_simple():
            print("\n🎯 Next steps:")
            print("1. Review app_simple_clean.py")
            print("2. If it looks good, replace the original:")
            print("   copy app_simple_clean.py app_simple.py")
            print("3. Start the backend: python app_simple.py")
        else:
            print("\n❌ Cleanup failed")
    except Exception as e:
        print(f"❌ Error: {e}")
