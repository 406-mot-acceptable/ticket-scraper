#!/usr/bin/env python3
import cgi
import cgitb
import sys
import os
import subprocess
import urllib.parse
import tempfile
from datetime import datetime

# Enable CGI error reporting
cgitb.enable()

# Print HTTP headers
print("Content-Type: text/plain")
print("Access-Control-Allow-Origin: *")
print()

def main():
    try:
        # Parse form data
        form = cgi.FieldStorage()
        ticket_url = form.getvalue("ticket_url", "").strip()
        
        if not ticket_url:
            print("ERROR: No URL provided")
            return
            
        if not ticket_url.startswith(('http://', 'https://')):
            print("ERROR: Invalid URL format. Must start with http:// or https://")
            return
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"scraped_ticket_{timestamp}.txt"
        
        # Path to the scraper script
        scraper_path = "/home/motty/ticket-scraper/splynx_scraper.py"
        output_path = f"/home/motty/web-share/{output_filename}"
        
        # Run the scraper
        cmd = [
            "python3", 
            scraper_path, 
            ticket_url, 
            "-o", output_path,
            "-t", "45000"  # 45 second timeout
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60,  # Overall timeout
            cwd="/home/motty/ticket-scraper"
        )
        
        if result.returncode == 0:
            # Extract character count from output
            lines = result.stdout.strip().split('\n')
            char_count = "unknown"
            for line in lines:
                if "Extracted" in line and "characters" in line:
                    char_count = line.split()[1]
                    break
                    
            print(f"SUCCESS: Ticket scraped successfully!")
            print(f"Output file: {output_filename}")
            print(f"Characters extracted: {char_count}")
        else:
            print(f"ERROR: Scraping failed")
            print(f"Error output: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("ERROR: Scraping timed out (60 seconds)")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()