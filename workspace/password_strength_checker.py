import re

def calculate_strength(password):
    """
    Calculate the strength of a password on a scale of 1-10.
    
    Parameters:
    - password: str, the password to evaluate
    
    Returns:
    - int, the strength rating of the password (1-10)
    """
    # Initialize strength score
    strength = 0
    
    # Check password length
    if len(password) >= 8:
        strength += 2
    if len(password) >= 12:
        strength += 2
    if len(password) >= 16:
        strength += 2
    
    # Check for uppercase letters
    if re.search(r'[A-Z]', password):
        strength += 1
    
    # Check for lowercase letters
    if re.search(r'[a-z]', password):
        strength += 1
    
    # Check for digits
    if re.search(r'\d', password):
        strength += 1
    
    # Check for special characters
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]', password):
        strength += 1
    
    # Normalize strength score to a scale of 1-10
    strength = min(strength, 10)
    strength = max(strength, 1)
    
    return strength

def main():
    """
    Main function to demonstrate password strength checker.
    """
    password = input("Enter a password to check its strength: ")
    try:
        strength = calculate_strength(password)
        print(f"Password strength: {strength}/10")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()