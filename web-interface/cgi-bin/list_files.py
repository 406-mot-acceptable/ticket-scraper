#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def main():
    try:
        web_dir = "/home/motty/web-share"
        files = []
        
        for filename in os.listdir(web_dir):
            filepath = os.path.join(web_dir, filename)
            if os.path.isfile(filepath) and not filename.startswith('.') and filename != 'index.html':
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'url': filename
                })
        
        # Sort by modification time, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        print(json.dumps({'files': files}))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}))

if __name__ == "__main__":
    main()