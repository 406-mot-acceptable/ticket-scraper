#!/usr/bin/env python3
"""
Splynx Public Ticket Scraper
Extracts ticket messages/comments and formats them for AI summarization
"""

import sys
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import argparse

def scrape_ticket(public_url, output_file=None, timeout=30000):
    """
    Scrape ticket data from Splynx public link and format for text output
    
    Args:
        public_url (str): The public ticket URL from Splynx
        output_file (str): Optional output file path
        timeout (int): Page load timeout in milliseconds
    """
    
    ticket_content = []
    timeline_events = []
    
    try:
        with sync_playwright() as p:
            # Launch browser (use chromium for speed)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set longer timeout for JS-heavy pages
            page.set_default_timeout(timeout)
            
            print(f"Loading ticket: {public_url}")
            page.goto(public_url)
            
            # Wait for the app to load and ticket content to appear
            # Adjust these selectors based on actual Splynx DOM structure
            page.wait_for_load_state('networkidle')
            
            # Give extra time for dynamic content
            page.wait_for_timeout(3000)
            
            # Extract ticket basic info
            try:
                ticket_title = page.locator('h1, .ticket-title, [class*="title"]').first.text_content(timeout=5000)
                ticket_content.append(f"=== TICKET: {ticket_title} ===\n")
            except:
                ticket_content.append("=== TICKET CONTENT ===\n")
            
            # Try multiple selectors for messages/comments
            message_selectors = [
                '.message, .comment',
                '[class*="message"]',
                '[class*="comment"]',
                '.ticket-message',
                '.conversation-item',
                '[data-testid*="message"]'
            ]
            
            messages_found = False
            
            for selector in message_selectors:
                try:
                    messages = page.locator(selector).all()
                    if messages:
                        print(f"Found {len(messages)} messages using selector: {selector}")
                        messages_found = True
                        
                        for i, message in enumerate(messages, 1):
                            # Extract message author
                            author_selectors = [
                                '.author, .sender, .from',
                                '[class*="author"]',
                                '[class*="sender"]',
                                'strong, .name, .username'
                            ]
                            
                            author = "Unknown"
                            for auth_sel in author_selectors:
                                try:
                                    author_elem = message.locator(auth_sel).first
                                    if author_elem.is_visible():
                                        author = author_elem.text_content().strip()
                                        break
                                except:
                                    continue
                            
                            # Extract message timestamp
                            timestamp_selectors = [
                                '.timestamp, .date, .time',
                                '[class*="timestamp"]',
                                '[class*="date"]'
                            ]
                            
                            timestamp = ""
                            for ts_sel in timestamp_selectors:
                                try:
                                    ts_elem = message.locator(ts_sel).first
                                    if ts_elem.is_visible():
                                        timestamp = f" - {ts_elem.text_content().strip()}"
                                        break
                                except:
                                    continue
                            
                            # Extract message body
                            message_body = message.text_content().strip()
                            
                            # Clean up the body (remove author/timestamp if they're included)
                            if author in message_body:
                                message_body = message_body.replace(author, "").strip()
                            
                            # Format message
                            ticket_content.append(f"\n--- Message {i} from {author}{timestamp} ---\n")
                            ticket_content.append(f"{message_body}\n")
                        
                        break
                        
                except Exception as e:
                    continue
            
            # If no messages found with standard selectors, try extracting all text
            if not messages_found:
                print("No messages found with standard selectors, extracting all visible text...")
                page_text = page.locator('body').text_content()
                ticket_content.append(f"\n--- Raw Page Content ---\n")
                ticket_content.append(page_text)
            
            browser.close()
            
    except Exception as e:
        print(f"Error scraping ticket: {e}")
        return None
    
    # Add timeline section if we found status changes
    if timeline_events:
        ticket_content.insert(1, f"\n=== TIMELINE ===\n")
        for event in timeline_events:
            ticket_content.insert(2, f"{event}\n")
        ticket_content.insert(2 + len(timeline_events), f"\n=== MESSAGES ===\n")
    
    # Join content and clean up
    final_content = ''.join(ticket_content)
    
    # Clean up extra whitespace
    final_content = re.sub(r'\n{3,}', '\n\n', final_content)
    
    # Output to file or stdout
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"Ticket content saved to: {output_file}")
        print(f"\nTo summarize with Claude Pro, paste this command:")
        print(f"cat {output_file}")
        print(f"Then copy the output and paste into Claude chat with: 'Summarize this ticket'")
    else:
        print("\n" + "="*50)
        print(final_content)
        print("\n" + "="*50)
        print("Copy the above text and paste into Claude chat for summarization")
    
    return final_content

def main():
    parser = argparse.ArgumentParser(description='Scrape Splynx public ticket')
    parser.add_argument('url', help='Public ticket URL')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-t', '--timeout', type=int, default=30000, 
                       help='Page load timeout in milliseconds (default: 30000)')
    
    args = parser.parse_args()
    
    if not args.url.startswith('http'):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)
    
    content = scrape_ticket(args.url, args.output, args.timeout)
    
    if content:
        print(f"\nExtracted {len(content)} characters")
        print("Ready for AI summarization!")
    else:
        print("Failed to extract ticket content")
        sys.exit(1)

if __name__ == "__main__":
    main()
