import httpx
import asyncio
import subprocess
import os
import sys
from typing import Dict, List, Any

class OsintService:
    """
    OSINT service integration with Tookie-OSINT.
    """
    
    def __init__(self):
        self.base_path = os.path.join(os.getcwd(), "tookie-osint")
        # Ensure tookie-osint directory exists
        if not os.path.exists(self.base_path):
             # Fallback if running from root instead of backend
             self.base_path = os.path.join(os.getcwd(), "backend", "tookie-osint")

    async def check_username(self, username: str) -> Dict[str, Any]:
        """Check if username exists using Tookie-OSINT"""
        results = []
        
        # Command to run brib.py
        # args: --username <user> --scan --fast (fast mode for speed)
        # We use --fast (mode 1) which uses fsites.json (fewer sites) to be quicker for a demo
        
        # Check if python3 or python is available
        python_cmd = sys.executable
        
        script_path = os.path.join(self.base_path, "brib.py")
        
        if not os.path.exists(script_path):
            return {"error": f"Tookie-OSINT script not found at {script_path}"}

        cmd = [
            python_cmd, 
            "brib.py", 
            "--username", username, 
            "--scan", 
            "--fast"
        ]
        
        try:
            # Run the process
            # We need to set cwd to the tookie-osint directory so it finds its modules
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.base_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Tookie saves output to ./captured/{username}.txt
            # Let's try to read that file
            output_file = os.path.join(self.base_path, "captured", f"{username}.txt")
            
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for line in lines:
                        # Tookie output format: "[+] Site: URL" or similar. 
                        # Based on brib.py logic, it prints results. 
                        # We need to parse the text file content.
                        # Assuming lines contain URLs of found profiles.
                        line = line.strip()
                        if line and "http" in line:
                            # Basic extraction
                            parts = line.split(" ")
                            for part in parts:
                                if part.startswith("http"):
                                    # Extract site name from URL
                                    from urllib.parse import urlparse
                                    domain = urlparse(part).netloc
                                    results.append({
                                        "site": domain,
                                        "url": part,
                                        "status": "found"
                                    })
            else:
                # Fallback: Try to parse stdout if file wasn't created
                # Tookie prints colorful output, might be hard to parse
                pass

        except Exception as e:
            return {"error": str(e)}
                    
        return {
            "username": username,
            "found_accounts": results,
            "total_checked": "Fast Scan Mode"
        }


