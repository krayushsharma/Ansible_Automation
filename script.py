import asyncio
import sys
import json
import subprocess
import os
import shutil

def verify_chromium():

    chrome_path = os.environ.get(
        "CHROME_PATH",
        "/tmp/chromium/chrome-linux/chrome"
    )

    print("\n==============================")
    print("CHROMIUM PRE-CHECK")
    print("==============================")
    print(f"Chrome Path: {chrome_path}")

    # Check file exists
    if not os.path.exists(chrome_path):
        print("[ERROR] Chromium binary not found")
        return False

    print("[OK] Chromium file exists")

    # Check execute permission
    if not os.access(chrome_path, os.X_OK):

        print("[WARNING] Execute permission missing")
        print("[*] Applying chmod +x")

        try:
            os.chmod(chrome_path, 0o755)
        except Exception as e:
            print(f"[ERROR] Unable to set execute permission: {e}")
            return False

    if not os.access(chrome_path, os.X_OK):
        print("[ERROR] Chromium still not executable")
        return False

    print("[OK] Execute permission verified")

    # Check version
    try:

        result = subprocess.run(
            [chrome_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20
        )

        print("[OK] Chromium Version:")
        print(result.stdout.strip())

    except Exception as e:
        print(f"[ERROR] Cannot execute Chromium: {e}")
        return False

    # Check dependencies

    # if shutil.which("ldd"):

    #     print("\nChecking shared libraries...")

    #     try:

    #         result = subprocess.run(
    #             ["ldd", chrome_path],
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.PIPE,
    #             text=True
    #         )

    #         missing = []

    #         for line in result.stdout.splitlines():

    #             if "not found" in line:
    #                 missing.append(line.strip())

    #         if missing:

    #             print("\n[ERROR] Missing Linux libraries detected:\n")

    #             for item in missing:
    #                 print(item)

    #             return False

    #         print("[OK] All shared libraries found")

    #     except Exception as e:
    #         print(f"[WARNING] Unable to run ldd: {e}")

    # Test headless startup

    print("\nTesting Chromium startup...")

    try:

        result = subprocess.run(
            [
                chrome_path,
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--dump-dom",
                "about:blank"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )

        if result.returncode != 0:

            print("[ERROR] Chromium startup test failed")

            print("\nSTDOUT:")
            print(result.stdout)

            print("\nSTDERR:")
            print(result.stderr)

            return False

        print("[OK] Chromium headless startup successful")

    except Exception as e:
        print(f"[ERROR] Chromium startup test failed: {e}")
        return False

    print("\n[OK] Chromium validation completed successfully")
    print("==============================\n")

    return True








chrome_path = os.environ.get(
    "CHROME_PATH",
    "/tmp/chromium/chrome-linux/chrome"
)

try:
    import pyppeteer
except ImportError:
    print("[*] Installing Pyppeteer...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyppeteer"])
    import pyppeteer
 
async def wait_for_element_with_text(page, selector, text, timeout=10000):
    """Wait for element to have text content (useful for waiting for AJAX data)"""
    try:
        await page.waitForFunction(
            f'''
            () => {{
                const el = document.querySelector('{selector}');
                return el && el.innerText.includes('{text}');
            }}
            ''',
            {'timeout': timeout}
        )
        return True
    except:
        return False
 
async def automate_ucs(username, password, output_dir="."):
    
    LOGIN_URL = "https://192.168.31.200/ui/faces/UCSCentral.xhtml"
    MAIN_URL = "https://192.168.31.200/ui/faces/UCSCentral.xhtml"
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("[*] Launching Pyppeteer browser...")
    browser = await pyppeteer.launch({
        'executablePath': chrome_path,
        'headless': True,
        'ignoreHTTPSErrors': True,
        'args': [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--ignore-certificate-errors',
            '--allow-running-insecure-content'
        ]   
    })
    
    try:
        page = await browser.newPage()
        
        # Ignore HTTPS errors
        await page.setBypassCSP(True)
        
        # Set viewport
        await page.setViewport({'width': 1920, 'height': 1080})
        
        print("[*] STEP 1 - Navigating to login page...")
        await page.goto(LOGIN_URL, {'waitUntil': 'domcontentloaded', 'timeout': 30000})
        await asyncio.sleep(1)
        
        print("[*] STEP 2 - Entering credentials...")
        await page.type('input[name="loginForm:userTxt"]', username, {'delay': 50})
        await page.type('input[name="loginForm:passwordTxt"]', password, {'delay': 50})
        
        # # Set domain to eu
        # await page.evaluate('''
        #     () => {
        #         const domainInput = document.querySelector('input[name="loginForm:domain_input"]');
        #         if (domainInput) {
        #             domainInput.value = "eu";
        #         }
        #     }
        # ''')

        # Save page HTML for debugging
        html = await page.content()

        with open("\tmp\login_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        print("[*] Login page HTML saved to D:\\VM\\login_page.html")

        # List all buttons and inputs
        buttons = await page.evaluate("""
        () => {
            return Array.from(document.querySelectorAll('input,button,a'))
                .map(el => ({
                    tag: el.tagName,
                    id: el.id,
                    name: el.name,
                    type: el.type || '',
                    value: el.value || '',
                    text: el.innerText || ''
                }));
        }
        """)

        print("\\n===== PAGE ELEMENTS =====")
        for b in buttons:
            print(b)

        print("===== END PAGE ELEMENTS =====\\n")

        
        print("[*] STEP 3 - Submitting login form (JSF postback)...")

        clicked = await page.evaluate("""
        () => {
            const btn = document.getElementById('loginForm:loginbtn');

            if (btn) {
                btn.click();
                return true;
            }

            return false;
        }
        """)

        print("Login button found:", clicked)

        await asyncio.sleep(10)

        print("Current URL:", page.url)
        print("Title:", await page.title())

        await page.screenshot({
            'path': '\tmp\after_login.png',
            'fullPage': True
        })

        html = await page.content()

        with open('\tmp\\after_login.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print("Saved after_login.html")
        
        # Check login status
        current_url = page.url
        if 'login' in current_url.lower():
            print("[X] LOGIN FAILED - Still on login page")
            return False
        
        print("[✓] Login successful")
        print(f"[*] Current URL: {current_url}")
        
        print("[*] STEP 4 - Navigating to main page...")
        await page.goto(MAIN_URL, {'waitUntil': 'domcontentloaded', 'timeout': 30000})
        await asyncio.sleep(3)
        
        print("[*] STEP 5 - Waiting for JSF page elements to load...")
        try:
            await page.waitForSelector('input[value="SERVERS"]', {'timeout': 15000})
        except:
            print("[!] Could not find SERVERS button, but continuing...")
        
        print("[*] STEP 6 - Opening Servers page...")

        result = await page.evaluate("""
        () => {

            // Find Servers menu item
            const links = document.querySelectorAll('a');

            for (const link of links) {

                if (link.innerText &&
                    link.innerText.trim().toUpperCase() === 'SERVERS') {

                    link.click();
                    return "clicked servers link";
                }
            }

            // fallback
            if (typeof selectTreeItem === 'function') {

                const selectedItem =
                    document.querySelector('.treeSelectedItem');

                if (selectedItem) {
                    selectedItem.value = 'SERVERS';
                }

                selectTreeItem();

                return "called selectTreeItem()";
            }

            return "servers link not found";
        }
        """)

        print("[*] Result:", result)

        await asyncio.sleep(10)

        print("[*] STEP 7 - Waiting for AJAX response and JavaScript to render data...")
        await asyncio.sleep(4)
        
        # Wait for actual server data to appear
        wait_success = await wait_for_element_with_text(
            page,
            'table tbody',
            '',
            5000
        )
        
        print("[*] STEP 8 - Extracting server data from rendered DOM...")
        
        # Extract server data from the rendered page
        server_data = await page.evaluate("""
            () => {
                const servers = [];
                
                // Method 1: Look for tables with server data
                const tables = document.querySelectorAll('table');
                
                for (let table of tables) {
                    const tbody = table.querySelector('tbody');
                    if (!tbody) continue;
                    
                    const rows = tbody.querySelectorAll('tr');
                    
                    if (rows.length > 0) {
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            
                            // Skip empty rows
                            if (cells.length === 0) return;
                            
                            // Check if row has actual content
                            const rowText = row.innerText.trim();
                            if (!rowText) return;
                            
                            const server = {
                                'name': cells[0]?.innerText.trim() || '',
                                'model': cells[1]?.innerText.trim() || '',
                                'serial': cells[2]?.innerText.trim() || '',
                                'ipaddress': cells[3]?.innerText.trim() || '',
                                'status': cells[4]?.innerText.trim() || '',
                                'raw_row': rowText.substring(0, 100)
                            };
                            
                            // Only add if has at least one field with data
                            if (server.name || server.model || server.serial) {
                                servers.push(server);
                            }
                        });
                    }
                }
                
                return {
                    'total': servers.length,
                    'servers': servers,
                    'timestamp': new Date().toISOString(),
                    'page_title': document.title,
                    'tables_found': document.querySelectorAll('table').length
                };
            }
        """)
        
        print(f"\n[✓] Found {server_data['total']} servers")
        print(f"[*] Page title: {server_data['page_title']}")
        print(f"[*] Tables found: {server_data['tables_found']}")
        
        # Export to JSON
        export_file = os.path.join(output_dir, "servers_export.json")
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(server_data, f, indent=2)
        
        print(f"\n[✓] Exported to {export_file}")
        
        if server_data['total'] > 0:
            print("\n[*] Server Details:")
            print("-" * 100)
            
            for i, server in enumerate(server_data['servers'], 1):
                print(f"\nServer {i}:")
                for key, value in server.items():
                    if key != 'raw_row':
                        print(f"  {key}: {value}")
            
            return True
        else:
            print("[!] No servers found in table")
            
            # Save screenshot for debugging
            screenshot_file = os.path.join(output_dir, "debug_screenshot.png")
            await page.screenshot({'path': screenshot_file})
            print(f"[*] Screenshot saved to {screenshot_file}")
            
            # Save HTML for debugging
            html_file = os.path.join(output_dir, "debug_page.html")
            html_content = await page.content()
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"[*] Page HTML saved to {html_file}")
            
            return False
    
    except Exception as e:
        print(f"[X] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await browser.close()
        print("[*] Browser closed")
 
if __name__ == "__main__":
    if not verify_chromium():
        print("[FATAL] Chromium validation failed")
    sys.exit(1)
    
    username = "admin"
    password = "12345678"
    output_dir = '/tmp/'
    
    success = asyncio.run(automate_ucs(username, password, output_dir))
    sys.exit(0 if success else 1)
 