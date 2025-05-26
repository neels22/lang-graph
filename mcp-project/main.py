# server.py
from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import random
from dataclasses import dataclass
from datetime import datetime

# Create an MCP server
mcp = FastMCP("Student Management System")

# Data structure for student information
@dataclass
class Student:
    roll_no: int
    name: str
    age: int
    grade: str
    subjects: List[str]
    created_at: datetime

# In-memory database to store students
students_db = {}

# Generate random student data
def generate_random_students(count: int = 10):
    first_names = ["John", "Emma", "Michael", "Sophia", "William", "Olivia", "James", "Ava", "Benjamin", "Isabella"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    subjects = ["Math", "Science", "English", "History", "Computer Science", "Physics", "Chemistry", "Biology"]
    grades = ["A", "B", "C", "D"]

    for i in range(count):
        roll_no = i + 1
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(15, 20)
        grade = random.choice(grades)
        student_subjects = random.sample(subjects, k=random.randint(3, 6))
        created_at = datetime.now()
        
        students_db[roll_no] = Student(
            roll_no=roll_no,
            name=name,
            age=age,
            grade=grade,
            subjects=student_subjects,
            created_at=created_at
        )

# Initialize with some random data
generate_random_students()

# Get student by roll number
@mcp.resource("student://{roll_no}")
def get_student_by_roll(roll_no: int) -> dict:
    """Get student information by roll number"""
    if roll_no not in students_db:
        return {"error": "Student not found"}
    student = students_db[roll_no]
    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "age": student.age,
        "grade": student.grade,
        "subjects": student.subjects,
        "created_at": student.created_at.isoformat()
    }

# Get student by name
@mcp.resource("student/name://{name}")
def get_student_by_name(name: str) -> List[dict]:
    """Get student information by name"""
    matching_students = []
    for student in students_db.values():
        if name.lower() in student.name.lower():
            matching_students.append({
                "roll_no": student.roll_no,
                "name": student.name,
                "age": student.age,
                "grade": student.grade,
                "subjects": student.subjects,
                "created_at": student.created_at.isoformat()
            })
    return matching_students

# Add new student
@mcp.tool()
def add_student(name: str, age: int, grade: str, subjects: List[str]) -> dict:
    """Add a new student to the database"""
    roll_no = max(students_db.keys()) + 1 if students_db else 1
    student = Student(
        roll_no=roll_no,
        name=name,
        age=age,
        grade=grade,
        subjects=subjects,
        created_at=datetime.now()
    )
    students_db[roll_no] = student
    return {
        "message": "Student added successfully",
        "roll_no": roll_no
    }

# Update student information
@mcp.tool()
def update_student(roll_no: int, name: Optional[str] = None, age: Optional[int] = None, 
                  grade: Optional[str] = None, subjects: Optional[List[str]] = None) -> dict:
    """Update student information"""
    if roll_no not in students_db:
        return {"error": "Student not found"}
    
    student = students_db[roll_no]
    if name:
        student.name = name
    if age:
        student.age = age
    if grade:
        student.grade = grade
    if subjects:
        student.subjects = subjects
    
    return {
        "message": "Student updated successfully",
        "roll_no": roll_no
    }

# Delete student
@mcp.tool()
def delete_student(roll_no: int) -> dict:
    """Delete a student from the database"""
    if roll_no not in students_db:
        return {"error": "Student not found"}
    
    del students_db[roll_no]
    return {
        "message": "Student deleted successfully",
        "roll_no": roll_no
    }

# List all students
@mcp.tool()
def list_all_students() -> List[dict]:
    """Get information about all students"""
    return [
        {
            "roll_no": student.roll_no,
            "name": student.name,
            "age": student.age,
            "grade": student.grade,
            "subjects": student.subjects,
            "created_at": student.created_at.isoformat()
        }
        for student in students_db.values()
    ]