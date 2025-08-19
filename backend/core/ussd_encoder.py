"""
USSD Encoder/Decoder for GSM 7-bit encoding.

This module provides functionality to encode and decode USSD commands
using GSM 7-bit encoding, which is required for proper USSD communication.
"""

import re
from typing import List, Tuple


class UssdEncoderDecoder:
    """
    USSD Encoder/Decoder for GSM 7-bit encoding.
    
    This class provides methods to encode USSD commands into GSM 7-bit format
    and decode responses from the same format.
    """
    
    # GSM 7-bit character set (standard GSM alphabet)
    GSM_7BIT_CHARS = {
        '@': 0x00, '£': 0x01, '$': 0x02, '¥': 0x03, 'è': 0x04, 'é': 0x05, 'ù': 0x06, 'ì': 0x07,
        'ò': 0x08, 'Ç': 0x09, '\n': 0x0A, 'Ø': 0x0B, 'ø': 0x0C, '\r': 0x0D, 'Å': 0x0E, 'å': 0x0F,
        'Δ': 0x10, '_': 0x11, 'Φ': 0x12, 'Γ': 0x13, 'Λ': 0x14, 'Ω': 0x15, 'Π': 0x16, 'Ψ': 0x17,
        'Σ': 0x18, 'Θ': 0x19, 'Ξ': 0x1A, ' ': 0x20, '!': 0x21, '"': 0x22, '#': 0x23, '¤': 0x24,
        '%': 0x25, '&': 0x26, "'": 0x27, '(': 0x28, ')': 0x29, '*': 0x2A, '+': 0x2B, ',': 0x2C,
        '-': 0x2D, '.': 0x2E, '/': 0x2F, '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, ':': 0x3A, ';': 0x3B, '<': 0x3C,
        '=': 0x3D, '>': 0x3E, '?': 0x3F, '¡': 0x40, 'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44,
        'E': 0x45, 'F': 0x46, 'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C,
        'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52, 'S': 0x53, 'T': 0x54,
        'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58, 'Y': 0x59, 'Z': 0x5A, 'Ä': 0x5B, 'Ö': 0x5C,
        'Ñ': 0x5D, 'Ü': 0x5E, '§': 0x5F, '¿': 0x60, 'a': 0x61, 'b': 0x62, 'c': 0x63, 'd': 0x64,
        'e': 0x65, 'f': 0x66, 'g': 0x67, 'h': 0x68, 'i': 0x69, 'j': 0x6A, 'k': 0x6B, 'l': 0x6C,
        'm': 0x6D, 'n': 0x6E, 'o': 0x6F, 'p': 0x70, 'q': 0x71, 'r': 0x72, 's': 0x73, 't': 0x74,
        'u': 0x75, 'v': 0x76, 'w': 0x77, 'x': 0x78, 'y': 0x79, 'z': 0x7A, 'ä': 0x7B, 'ö': 0x7C,
        'ñ': 0x7D, 'ü': 0x7E, 'à': 0x7F
    }
    
    # Reverse mapping for decoding
    GSM_7BIT_CHARS_REVERSE = {v: k for k, v in GSM_7BIT_CHARS.items()}
    
    @classmethod
    def encode_as_7bit_gsm(cls, text: str) -> str:
        """
        Encode text as GSM 7-bit format.
        
        Args:
            text: Text to encode
            
        Returns:
            Encoded text in GSM 7-bit format
        """
        if not text:
            return ""
        
        # Convert to uppercase for better compatibility
        text = text.upper()
        
        # Encode each character
        encoded_chars = []
        for char in text:
            if char in cls.GSM_7BIT_CHARS:
                encoded_chars.append(char)
            else:
                # Replace unsupported characters with space
                encoded_chars.append(' ')
        
        return ''.join(encoded_chars)
    
    @classmethod
    def encode_as_hex_7bit_gsm(cls, text: str) -> str:
        """
        Encode text as GSM 7-bit hex format.
        
        Args:
            text: Text to encode
            
        Returns:
            Hex-encoded text in GSM 7-bit format
        """
        if not text:
            return ""
        
        # Convert to uppercase for better compatibility
        text = text.upper()
        
        # Encode each character to hex
        hex_chars = []
        for char in text:
            if char in cls.GSM_7BIT_CHARS:
                hex_value = cls.GSM_7BIT_CHARS[char]
                hex_chars.append(f"{hex_value:02X}")
            else:
                # Replace unsupported characters with space
                hex_chars.append("20")
        
        return ''.join(hex_chars)
    
    @classmethod
    def decode_from_7bit_gsm(cls, encoded_text: str) -> str:
        """
        Decode text from GSM 7-bit format.
        
        Args:
            encoded_text: Encoded text to decode
            
        Returns:
            Decoded text
        """
        if not encoded_text:
            return ""
        
        # Decode each character
        decoded_chars = []
        for char in encoded_text:
            if char in cls.GSM_7BIT_CHARS_REVERSE:
                decoded_chars.append(char)
            else:
                # Keep unknown characters as is
                decoded_chars.append(char)
        
        return ''.join(decoded_chars)
    
    @classmethod
    def decode_from_hex_7bit_gsm(cls, hex_text: str) -> str:
        """
        Decode text from GSM 7-bit hex format.
        
        Args:
            hex_text: Hex-encoded text to decode
            
        Returns:
            Decoded text
        """
        if not hex_text:
            return ""
        
        # Convert hex pairs to characters
        decoded_chars = []
        for i in range(0, len(hex_text), 2):
            if i + 1 < len(hex_text):
                hex_pair = hex_text[i:i+2]
                try:
                    char_code = int(hex_pair, 16)
                    if char_code in cls.GSM_7BIT_CHARS_REVERSE:
                        decoded_chars.append(cls.GSM_7BIT_CHARS_REVERSE[char_code])
                    else:
                        # Keep unknown characters as is
                        decoded_chars.append(chr(char_code))
                except ValueError:
                    # Invalid hex, keep as is
                    decoded_chars.append(hex_pair)
        
        return ''.join(decoded_chars)
    
    @classmethod
    def is_gsm_7bit_compatible(cls, text: str) -> bool:
        """
        Check if text is compatible with GSM 7-bit encoding.
        
        Args:
            text: Text to check
            
        Returns:
            True if text is compatible
        """
        if not text:
            return True
        
        for char in text:
            if char not in cls.GSM_7BIT_CHARS:
                return False
        
        return True
    
    @classmethod
    def sanitize_for_ussd(cls, text: str) -> str:
        """
        Sanitize text for USSD commands.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove any non-USSD characters
        # USSD commands typically contain: 0-9, *, #, +, and some letters
        sanitized = re.sub(r'[^0-9*#+A-Za-z]', '', text)
        
        # Convert to uppercase
        return sanitized.upper()
