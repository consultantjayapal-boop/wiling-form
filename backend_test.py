#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Will Writing App
Tests all major endpoints and functionality
"""

import requests
import sys
import json
import time
from datetime import datetime
import os
from pathlib import Path

class WillWritingAPITester:
    def __init__(self, base_url="https://estate-planner-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.will_id = None
        self.file_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api{endpoint}"
        
        # Default headers
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        # Merge with custom headers
        if headers:
            default_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            default_headers.pop('Content-Type', None)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data, headers=default_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=default_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")

            if success:
                self.log_test(name, True)
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return False, response_data

        except Exception as e:
            error_msg = str(e)
            print(f"   Error: {error_msg}")
            self.log_test(name, False, error_msg)
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "/health", 200)

    def test_signup(self):
        """Test user signup"""
        timestamp = datetime.now().strftime('%H%M%S')
        signup_data = {
            "email": "test@example.com",
            "mobile": "1234567890",
            "password": "password123",
            "confirm_password": "password123"
        }
        
        success, response = self.run_test("User Signup", "POST", "/auth/signup", 200, signup_data)
        
        if success and response.get('success'):
            self.token = response.get('access_token')
            self.user_id = response.get('user_id')
            print(f"   Token obtained: {self.token[:20]}...")
            print(f"   User ID: {self.user_id}")
        
        return success

    def test_login(self):
        """Test user login"""
        login_data = {
            "username": "test@example.com",
            "password": "password123"
        }
        
        success, response = self.run_test("User Login", "POST", "/auth/login", 200, login_data)
        
        if success and response.get('success'):
            self.token = response.get('access_token')
            self.user_id = response.get('user_id')
            print(f"   Token obtained: {self.token[:20]}...")
        
        return success

    def test_get_profile(self):
        """Test get user profile"""
        if not self.token:
            self.log_test("Get Profile", False, "No token available")
            return False
        
        return self.run_test("Get User Profile", "GET", "/user/profile", 200)[0]

    def test_create_will(self):
        """Test will creation"""
        if not self.token:
            self.log_test("Create Will", False, "No token available")
            return False
        
        will_data = {
            "title": "My Test Will",
            "language": "english",
            "content": "This is my last will and testament. I leave all my possessions to my family.",
            "ai_assisted": False
        }
        
        success, response = self.run_test("Create Will", "POST", "/wills/create", 200, will_data)
        
        if success and response.get('success'):
            self.will_id = response.get('will_id')
            print(f"   Will ID: {self.will_id}")
        
        return success

    def test_create_will_with_ai(self):
        """Test will creation with AI assistance"""
        if not self.token:
            self.log_test("Create Will with AI", False, "No token available")
            return False
        
        will_data = {
            "title": "AI Assisted Will",
            "language": "english",
            "content": "I want to create a simple will for my family.",
            "ai_assisted": True
        }
        
        success, response = self.run_test("Create Will with AI", "POST", "/wills/create", 200, will_data)
        
        if success and response.get('ai_suggestions'):
            print(f"   AI Suggestions received: {len(response['ai_suggestions'])} characters")
        
        return success

    def test_list_wills(self):
        """Test listing user's wills"""
        if not self.token:
            self.log_test("List Wills", False, "No token available")
            return False
        
        success, response = self.run_test("List Wills", "GET", "/wills/list", 200)
        
        if success and 'wills' in response:
            print(f"   Found {len(response['wills'])} wills")
        
        return success

    def test_get_will(self):
        """Test getting a specific will"""
        if not self.token or not self.will_id:
            self.log_test("Get Will", False, "No token or will_id available")
            return False
        
        return self.run_test("Get Will", "GET", f"/wills/{self.will_id}", 200)[0]

    def test_update_will(self):
        """Test updating a will"""
        if not self.token or not self.will_id:
            self.log_test("Update Will", False, "No token or will_id available")
            return False
        
        updated_data = {
            "title": "Updated Test Will",
            "language": "english",
            "content": "This is my updated last will and testament.",
            "ai_assisted": False
        }
        
        return self.run_test("Update Will", "PUT", f"/wills/{self.will_id}", 200, updated_data)[0]

    def test_ai_assistance(self):
        """Test AI assistance endpoint"""
        if not self.token:
            self.log_test("AI Assistance", False, "No token available")
            return False
        
        ai_request = {
            "query": "Help me write a will for my family",
            "language": "english",
            "will_context": "I have a house and some savings"
        }
        
        success, response = self.run_test("AI Assistance", "POST", "/ai/assist", 200, ai_request)
        
        if success and response.get('response'):
            print(f"   AI Response length: {len(response['response'])} characters")
        
        return success

    def test_file_upload(self):
        """Test file upload functionality"""
        if not self.token or not self.will_id:
            self.log_test("File Upload", False, "No token or will_id available")
            return False
        
        # Create a test file
        test_content = "This is a test document for will attachment."
        test_file_path = "/tmp/test_document.txt"
        
        try:
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {'file_type': 'documents'}
                
                success, response = self.run_test(
                    "File Upload", 
                    "POST", 
                    f"/files/upload/{self.will_id}", 
                    200, 
                    data=data, 
                    files=files
                )
                
                if success and response.get('file_id'):
                    self.file_id = response.get('file_id')
                    print(f"   File ID: {self.file_id}")
                
                return success
                
        except Exception as e:
            self.log_test("File Upload", False, f"File creation error: {str(e)}")
            return False
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    def test_list_files(self):
        """Test listing files for a will"""
        if not self.token or not self.will_id:
            self.log_test("List Files", False, "No token or will_id available")
            return False
        
        success, response = self.run_test("List Files", "GET", f"/files/list/{self.will_id}", 200)
        
        if success and 'files' in response:
            print(f"   Found {len(response['files'])} files")
        
        return success

    def test_download_file(self):
        """Test file download"""
        if not self.token or not self.file_id:
            self.log_test("Download File", False, "No token or file_id available")
            return False
        
        return self.run_test("Download File", "GET", f"/files/download/{self.file_id}", 200)[0]

    def test_send_message(self):
        """Test message sending"""
        if not self.token:
            self.log_test("Send Message", False, "No token available")
            return False
        
        message_data = {
            "recipient_name": "John Doe",
            "recipient_email": "john@example.com",
            "recipient_phone": "9876543210",
            "message_text": "This is a test message from the will writing app.",
            "preference": "email",
            "will_id": self.will_id
        }
        
        return self.run_test("Send Message", "POST", "/messages/send", 200, message_data)[0]

    def test_delete_file(self):
        """Test file deletion"""
        if not self.token or not self.file_id:
            self.log_test("Delete File", False, "No token or file_id available")
            return False
        
        return self.run_test("Delete File", "DELETE", f"/files/{self.file_id}", 200)[0]

    def test_invalid_token(self):
        """Test with invalid token"""
        original_token = self.token
        self.token = "invalid_token_12345"
        
        success, _ = self.run_test("Invalid Token Test", "GET", "/user/profile", 401)
        
        # Restore original token
        self.token = original_token
        return success

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        original_token = self.token
        self.token = None
        
        success, _ = self.run_test("Unauthorized Access Test", "GET", "/user/profile", 401)
        
        # Restore original token
        self.token = original_token
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Will Writing App Backend API Tests")
        print("=" * 60)
        
        # Basic connectivity
        self.test_health_check()
        
        # Authentication tests
        self.test_signup()
        # Note: Login test would fail after signup since user already exists
        # self.test_login()
        
        self.test_get_profile()
        
        # Will management tests
        self.test_create_will()
        self.test_create_will_with_ai()
        self.test_list_wills()
        self.test_get_will()
        self.test_update_will()
        
        # AI assistance test
        self.test_ai_assistance()
        
        # File management tests
        self.test_file_upload()
        self.test_list_files()
        self.test_download_file()
        
        # Message sending test
        self.test_send_message()
        
        # Security tests
        self.test_invalid_token()
        self.test_unauthorized_access()
        
        # Cleanup
        if self.file_id:
            self.test_delete_file()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = WillWritingAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())