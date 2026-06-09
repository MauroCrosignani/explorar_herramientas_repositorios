#!/usr/bin/env python3
import os
import sys
import json
import http.server
import socketserver
import webbrowser

PORT = 8000

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Intercept POST API calls from the browser dashboard."""
        if self.path == '/api/toggle-read':
            try:
                # Read content length and parse incoming JSON payload
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))
                
                item_id = payload.get('id')
                is_read = payload.get('read')
                
                if item_id is None or is_read is None:
                    self.send_error_response(400, "Missing id or read state parameters.")
                    return
                
                # Locate and update the database file
                script_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(script_dir, "data", "db.json")
                
                if not os.path.exists(db_path):
                    self.send_error_response(404, "Database file not found.")
                    return
                
                # Read current database
                with open(db_path, "r", encoding="utf-8") as f:
                    db = json.load(f)
                
                # Find the target item and update its read state
                item_found = False
                for item in db.get("historical_items", []):
                    if item.get("id") == item_id:
                        item["read"] = is_read
                        item_found = True
                        break
                
                if not item_found:
                    self.send_error_response(404, f"Item with ID '{item_id}' not found in database.")
                    return
                
                # Write updated database back to file
                with open(db_path, "w", encoding="utf-8") as f:
                    json.dump(db, f, indent=2, ensure_ascii=False)
                
                # Send successful response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                response = {"status": "success", "message": f"Updated read state of {item_id} to {is_read}."}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"[API] Updated item {item_id}: read={is_read}")
                
            except Exception as e:
                print(f"[API Error] Failed to process read toggle: {e}", file=sys.stderr)
                self.send_error_response(500, f"Internal Server Error: {str(e)}")
        else:
            self.send_error_response(404, "Endpoint not found.")

    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        err = {"status": "error", "message": message}
        self.wfile.write(json.dumps(err).encode('utf-8'))

def main():
    # Make sure we serve files from the project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Configure socket serving
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            print("==========================================================")
            print(f" Briefing.DS Local Server is active on port {PORT}")
            print(f" Dashboard URL: http://localhost:{PORT}/dashboard/index.html")
            print("==========================================================")
            print("Press Ctrl+C to terminate the local server.\n")
            
            # Automatically open browser to the dashboard URL
            dashboard_url = f"http://localhost:{PORT}/dashboard/index.html"
            print(f"[Launcher] Opening default browser to: {dashboard_url}")
            webbrowser.open(dashboard_url)
            
            # Start serving requests
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n[Server] Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"[Server Error] Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
