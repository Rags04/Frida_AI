import os

def convert_zip_to_folder(ipa_file_path):
    
    if not ipa_file_path.lower().endswith('.ipa'):
        print(f"Error: The provided path does not have ipa file"):
        return
    
    if not os.path.exists(ipa_file_path):
        print(f"File not found")
        return
    
    