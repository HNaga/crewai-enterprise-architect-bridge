import os
from crewai import Agent, Task, Crew, LLM
from ea_tools_final import EnterpriseArchitectToolFinal
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = LLM(
    model=MODEL,
    api_key=GEMINI_API_KEY
 )

# 1. CONFIG
# This matches the file that successfully worked in your test
EA_FILE_PATH = r"D:\Development\ba_po\AI_Enterprise_System.eapx"

# 2. AGENT
architect = Agent(
    role='Systems Architect',
    goal='Design UML models in Enterprise Architect.',
    backstory="You are an expert in EA. You use standard types (Actor, UseCase, Class, Requirement) to build robust systems.",
    tools=[EnterpriseArchitectToolFinal()],
    llm=llm,
    verbose=True
)

# 3. TASK
task_description = f"""
Design a "Ride Sharing System" (like Uber).

Create a JSON structure for the tool using this EXACT schema:

{{
    "package_name": "Ride Sharing System",
    "diagram_name": "Context Diagram",
    "elements": [
        {{ "name": "Passenger", "type": "Actor", "description": "App user" }},
        {{ "name": "Driver", "type": "Actor", "description": "Vehicle operator" }},
        {{ "name": "Request Ride", "type": "UseCase", "description": "User books a trip", 
           "scenarios": [ {{ "name": "Basic Path", "steps": ["Open App", "Enter Dest", "Confirm"] }} ] 
        }},
        {{ "name": "Accept Ride", "type": "UseCase", "description": "Driver accepts job" }},
        {{ "name": "Process Payment", "type": "UseCase", "description": "Money transfer" }},
        {{ "name": "Ride_Ticket", "type": "Class", "stereotype": "table", 
           "attributes": ["RideID", "Amount", "Status"] }}
    ],
    "connectors": [
        {{ "source": "Passenger", "target": "Request Ride", "type": "Association" }},
        {{ "source": "Driver", "target": "Accept Ride", "type": "Association" }},
        {{ "source": "Request Ride", "target": "Process Payment", "type": "Dependency" }}
    ]
}}

Send this JSON to the file path: "{EA_FILE_PATH}"
"""

design_task = Task(
    description=task_description,
    expected_output="Confirmation that the Ride Sharing model was created in EA.",
    agent=architect
)

# 4. EXECUTE
if __name__ == "__main__":
    print("\n🤖 Starting CrewAI...")
    crew = Crew(agents=[architect], tasks=[design_task], verbose=True)
    result = crew.kickoff()
    print("\n✅ DONE! Open Enterprise Architect to view the 'Ride Sharing System' package.")