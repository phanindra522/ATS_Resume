#!/usr/bin/env python3
"""
Debug script to test experience extraction patterns
"""

import re

def test_resume_extraction():
    """Test resume experience extraction patterns"""
    print("🔍 Debug: Resume Experience Extraction")
    print("=" * 50)
    
    test_text = """
    Jane Smith
    Digital Marketing Manager
    
    Experience:
    - 5 years of marketing experience
    - 3 years in digital marketing roles
    - Led marketing campaigns with $500K+ budgets
    - Managed social media marketing across multiple platforms
    """
    
    text_lower = test_text.lower()
    print(f"Text to analyze:\n{text_lower}\n")
    
    years_patterns = [
        (r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', "years of experience"),
        (r'(\d+)\+?\s*years?\s*(?:in|of)', "years in/of"),
        (r'(\d+)\+?\s*years?\s*(?:working|developing|building)', "years working/developing"),
        (r'experience[:\s]*(\d+)\+?\s*years?', "experience: X years"),
        (r'(\d+)\+?\s*years?\s*(?:professional|relevant)', "years professional/relevant"),
        (r'(\d+)\+?\s*years?\s*(?:marketing|business)', "years marketing/business"),
    ]
    
    print("Pattern matching results:")
    years_found = []
    
    for pattern, description in years_patterns:
        matches = re.findall(pattern, text_lower)
        print(f"  {description}: {matches}")
        for match in matches:
            try:
                years = int(match)
                if 0 <= years <= 50:
                    years_found.append(years)
            except ValueError:
                continue
    
    print(f"\nYears found: {years_found}")
    print(f"Max years: {max(years_found) if years_found else 'None'}")


def test_job_extraction():
    """Test job requirements extraction"""
    print("\n🔍 Debug: Job Requirements Extraction")
    print("=" * 50)
    
    requirements = [
        "Bachelor's degree in Marketing, Business, or related field",
        "4-6 years of marketing experience",
        "Experience with digital marketing channels and tools",
        "Strong analytical skills and data-driven mindset"
    ]
    
    requirements_text = ' '.join(requirements).lower()
    print(f"Requirements text:\n{requirements_text}\n")
    
    years_patterns = [
        (r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)', "years of experience"),
        (r'(\d+)\+?\s*years?\s*(?:in|of)', "years in/of"),
        (r'(\d+)\+?\s*years?\s*(?:working|developing|building)', "years working/developing"),
        (r'experience[:\s]*(\d+)\+?\s*years?', "experience: X years"),
        (r'minimum[:\s]*(\d+)\+?\s*years?', "minimum X years"),
        (r'at\s*least[:\s]*(\d+)\+?\s*years?', "at least X years"),
        (r'(\d+)\+?\s*years?\s*(?:marketing|business|management|industry)', "years marketing/business"),
        (r'(\d+)[-–](\d+)\s*years?\s*(?:of\s*)?(?:experience|exp|marketing)', "range years"),
    ]
    
    print("Pattern matching results:")
    years_found = []
    
    for pattern, description in years_patterns:
        matches = re.findall(pattern, requirements_text)
        print(f"  {description}: {matches}")
        for match in matches:
            try:
                if isinstance(match, tuple):
                    # Handle range patterns like "4-6 years" 
                    years = int(match[0])  # Take the minimum of the range
                else:
                    years = int(match)
                
                if 0 <= years <= 50:
                    years_found.append(years)
            except (ValueError, IndexError):
                continue
    
    print(f"\nYears found: {years_found}")
    print(f"Max years: {max(years_found) if years_found else 'None'}")


if __name__ == "__main__":
    test_resume_extraction()
    test_job_extraction()