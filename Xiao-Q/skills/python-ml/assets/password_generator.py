"""
Password Generator - Complete Example
Generates secure random passwords.
"""

import random
import string


def generate_password(length, use_upper=True, use_lower=True,
                     use_digits=True, use_symbols=True):
    """
    Generate a random password of the specified length.

    Args:
        length: Length of the password.
        use_upper: Include uppercase letters.
        use_lower: Include lowercase letters.
        use_digits: Include digits.
        use_symbols: Include punctuation symbols.

    Returns:
        A randomly generated password string.
    """
    chars = ""
    if use_upper:
        chars += string.ascii_uppercase
    if use_lower:
        chars += string.ascii_lowercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += string.punctuation

    if chars == "":
        raise ValueError("At least one character type must be selected!")

    password = ""
    for _ in range(length):
        password += random.choice(chars)
    return password


def generate_multiple(count, length, **kwargs):
    """Generate multiple passwords."""
    return [generate_password(length, **kwargs) for _ in range(count)]


def main():
    """Main program loop."""
    print("=== Password Generator ===")
    try:
        num = int(input("How many passwords? "))
        length = int(input("How many characters? "))
    except ValueError:
        print("Please enter valid numbers!")
        return

    passwords = generate_multiple(num, length)
    print("\n--- Your Passwords ---")
    for i, pw in enumerate(passwords, 1):
        print(f"{i}. {pw}")


if __name__ == "__main__":
    main()
