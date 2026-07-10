from pathlib import Path

APP_NAME = "Citi Homes P&C Administration System"
COMPANY_NAME = "CITI HOMES"
APP_VERSION = "1.0.0"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "citi_homes_hris.db"
ATTENDANCE_PORTAL_URL = "https://citi-homes.github.io/Attendance.Portal/index.html"
ATTENDANCE_SUPABASE_URL = "https://mnfrbyzdubsgnhxrzuxx.supabase.co"
ATTENDANCE_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1uZnJieXpkdWJzZ25oeHJ6dXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIyODUxMjQsImV4cCI6MjA5Nzg2MTEyNH0.XCVsDFy6-DDBEh847kH2AxfsCaxiFVFK-JZnxo6xPSI"

BRAND_COLORS = {
    "navy": "#0F172A",
    "blue": "#2563EB",
    "cyan": "#06B6D4",
    "green": "#16A34A",
    "amber": "#F59E0B",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "light": "#F8FAFC",
    "border": "#E2E8F0",
}

DEPARTMENTS = [
    "Management", "P&C", "Administration", "Production", "Upholstery", "Carpentry",
    "Painting", "Warehouse", "Procurement", "Finance", "Sales", "Maintenance", "Security"
]

DESIGNATIONS = [
    "P&C & Admin Executive", "Production Manager", "Production Incharge", "Carpenter",
    "Upholsterer", "Upholstery Stitcher", "Painter", "Machine Operator", "Forklift Driver",
    "Helper", "Warehouse Assistant", "Driver", "Cleaner", "Security Guard", "Accountant"
]

RECRUITMENT_STATUS = [
    "Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected",
    "Offer Sent", "Joined", "Rejected", "Hold"
]

TASK_STATUS = ["Pending", "In Progress", "Completed", "Hold"]
BILL_STATUS = ["Pending", "Submitted", "Paid"]
DOC_STATUS = ["Valid", "Expiring Soon", "Expired"]
PRIORITY = ["Low", "Medium", "High", "Critical"]
EMPLOYMENT_TYPES = ["Employee", "Contract", "Temporary", "Intern"]
VISA_STATUS = ["Not Started", "Processing", "Issued", "Renewal", "On Hold", "Cancelled"]
LEAVE_TYPES = ["Annual Leave", "Sick Leave", "Emergency Leave", "Unpaid Leave"]
CHECKLIST_STATUS = ["Pending", "Received", "Not Applicable"]
