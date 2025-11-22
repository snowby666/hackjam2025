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
        # Locate brib.py by searching relative to current working directory
        current_dir = os.getcwd()
        possible_paths = [
            os.path.join(current_dir, "tookie-osint"),
            os.path.join(current_dir, "backend", "tookie-osint"),
            # Direct path found via search
            os.path.abspath(os.path.join(current_dir, "backend", "tookie-osint")) 
        ]
        
        self.base_path = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "brib.py")):
                self.base_path = path
                break
        
        if not self.base_path:
             # Last resort: try to find it recursively
             import glob
             files = glob.glob("**/brib.py", recursive=True)
             if files:
                 self.base_path = os.path.dirname(os.path.abspath(files[0]))
        
        if not self.base_path:
            print("Warning: Could not find tookie-osint/brib.py directory")
            self.base_path = os.path.join(os.getcwd(), "tookie-osint") # Default fallback

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
            # Run the process using asyncio.to_thread and subprocess.run to avoid Windows asyncio loop issues
            # This bypasses the NotImplementedError with SelectorEventLoop on Windows
            def run_sync_subprocess():
                # Set PYTHONIOENCODING to utf-8 to avoid UnicodeEncodeError on Windows consoles
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                # Note: This is a synchronous blocking call that waits for the process to finish
                # The OSINT scan can take a long time (minutes), which might cause the web server 
                # to timeout the request if it exceeds the server's timeout settings.
                # However, since we're running this in a thread (asyncio.to_thread), 
                # the main event loop shouldn't be blocked, but the HTTP client might time out.
                return subprocess.run(
                    cmd,
                    cwd=self.base_path,
                    capture_output=True,
                    env=env,
                    stdin=subprocess.DEVNULL, # Ensure non-interactive mode to prevent hanging on prompts
                    text=True, # Process output as text (string) instead of bytes
                    encoding='utf-8' # Explicitly use UTF-8 for input/output
                )

            result = await asyncio.to_thread(run_sync_subprocess)
            
            stdout = result.stdout
            stderr = result.stderr
            
            if result.returncode != 0:
                 error_msg = stderr if stderr else "Unknown error"
                 print(f"Tookie-OSINT failed: {error_msg}")
                 return {"error": f"OSINT tool failed with code {result.returncode}: {error_msg}"}

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
                print(f"Output file not found: {output_file}")
                # Try to see if stdout has info
                stdout_str = stdout.decode() if stdout else ""
                if stdout_str:
                     # Parse stdout
                     pass

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"{str(e)}"}
        
        # Fetch content for found accounts asynchronously
        if results:
            try:
                async with httpx.AsyncClient(verify=False) as client:
                    tasks = [self._fetch_page_content(client, res['url']) for res in results]
                    contents = await asyncio.gather(*tasks)
                    
                    for res, content in zip(results, contents):
                        if content:
                            res['page_summary'] = content
            except Exception as e:
                print(f"Error fetching page contents: {e}")

        print(f"Results: {results}")
        return {
            "username": username,
            "found_accounts": results,
            "total_checked": "Fast Scan Mode"
        }

    async def _fetch_page_content(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch and summarize page content"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = await client.get(url, headers=headers, timeout=5.0, follow_redirects=True)
            
            if response.status_code == 200:
                content = response.text
                
                # Clean HTML
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Remove noise
                    for tag in soup(["script", "style", "meta", "link", "noscript", "header", "footer", "nav"]):
                        tag.extract()
                        
                    text = soup.get_text(separator=' ', strip=True)
                except ImportError:
                    # Fallback if bs4 missing
                    import re
                    text = re.sub(r'<[^>]+>', ' ', content)
                    text = re.sub(r'\s+', ' ', text).strip()
                
                # Truncate to keep it brief (200 chars)
                if len(text) > 200:
                    return text[:200] + "..."
                return text
        except Exception:
            pass
        return None


