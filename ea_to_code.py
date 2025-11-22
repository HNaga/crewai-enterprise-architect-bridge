import os
from crewai import Agent, Task, Crew, Process, LLM
from ea_tools_final import EnterpriseArchitectToolFinal
from file_tools import FileWriteTool # Import the new tool
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("MODEL")
API_KEY = os.getenv("GEMINI_API_KEY")
llm = LLM(
    model=MODEL,
    api_key=API_KEY,
    temperature=0.7,
    max_tokens=2048,
    top_p=0.95,
    frequency_penalty=0.0,
    presence_penalty=0.0,
)

# CONFIG
EA_FILE_PATH = r"D:\Development\ba_po\AI_Enterprise_System.eapx"

# --- AGENTS ---

# 1. The Architect (Builds the EA Model)
architect = Agent(
    role='Solution Architect',
    goal='Design the system in Enterprise Architect.',
    backstory="You define the structure. You create Classes with attributes in EA.",
    tools=[EnterpriseArchitectToolFinal()],
    verbose=True,
    llm=llm
)

# 2. The Developer (Writes the Code)
developer = Agent(
    role='Senior Python Developer',
    goal='Write working code based on the Architect\'s design.',
    backstory="""
    You take the Classes and Attributes defined by the Architect and turn them into actual Python code (Flask API).
    You also write the SQL schema.
    """,
    tools=[FileWriteTool()],
    verbose=True,
    llm=llm
)

# 3. The DevOps (Prepares Deployment)
devops = Agent(
    role='DevOps Engineer',
    goal='Prepare the application for deployment.',
    backstory="You generate Dockerfiles and requirements.txt so the app can run anywhere.",
    tools=[FileWriteTool()],
    verbose=True,
    llm=llm
)

# --- TASKS ---

# Task 1: Modeling (EA)
model_task = Task(
    description=f"""
    Design a "Library Inventory System".
    
    Use the EA Tool to build:
    1. Package: "Library Code Spec"
    2. Class: "Book" (Attributes: id, title, author, isbn, is_published)
    3. Class: "Member" (Attributes: id, name, email)
    
    Output the JSON used for the tool.
    Path: "{EA_FILE_PATH}"
    """,
    expected_output="Confirmation that EA Model is built.",
    agent=architect
)

# Task 2: Coding (Python)
code_task = Task(
    description="""
    Look at the "Book" and "Member" classes defined by the Architect.
    
    1. Write a **Flask API** (`app.py`) that includes:
       - A SQLAlchemy Model for 'Book' and 'Member'.
       - A GET route to list books.
       - A POST route to add a book.
    
    2. Use the 'Code Writer' tool to save this file as `app.py`.
    """,
    expected_output="A valid Python file named app.py.",
    agent=developer,
    context=[model_task] # Needs to know what the Architect designed
)

# Task 3: Deployment (Docker)
deploy_task = Task(
    description="""
    Create the deployment configuration.
    1. Create a `requirements.txt` (flask, sqlalchemy).
    2. Create a `Dockerfile` to run the `app.py`.
    
    Use the 'Code Writer' tool to save these files.
    """,
    expected_output="Dockerfile and requirements.txt created.",
    agent=devops
)

# --- EXECUTION ---
if __name__ == "__main__":
    crew = Crew(
        agents=[architect, developer, devops],
        tasks=[model_task, code_task, deploy_task],
        verbose=True,
        process=Process.sequential
    )
    crew.kickoff()
    print("\n✅ FULL CYCLE COMPLETE!")
    print("1. Check EA for the Diagrams.")
    print("2. Check 'D:\\Development\\ba_po\\output' for the Source Code.")