from typing import TypedDict
import os
from dotenv import load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

# Load environment
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI()

# Test LLM
print(llm.invoke("What is the capital of France?").content)

# Define the state
class State(TypedDict):
    application: str
    experience_level: str
    skill_match: str
    job_title: str
    response: str

# Create the workflow graph
workflow = StateGraph(State)

# ---- Define Node Functions ---- #

def categorize_experience(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Based on the following job application, categorize the experience level of the user as 'entry level', 'mid level', or 'senior level':\n\nApplication: {application}"
    )
    chain = prompt | llm
    experience_level = chain.invoke({"application": state["application"]}).content.strip().lower()
    print("This is experience level:", experience_level)
    return {**state, "experience_level": experience_level}

def assess_skill_match(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        "Based on the following job application for a Python Developer, assess the skill match of the user as 'match' or 'no match':\n\nApplication: {application}"
    )
    chain = prompt | llm
    skill_match = chain.invoke({"application": state["application"]}).content.strip().lower()
    print("This is skill match:", skill_match)
    return {**state, "skill_match": skill_match}

def schedule_hr_interview(state: State) -> State:
    print("Scheduling an interview with the user...")
    return {**state, "response": "candidate shortlisted for HR interview!"}

def escalate_to_manager(state: State) -> State:
    print("Escalating the application to the manager...")
    return {**state, "response": "candidate escalated to manager for review!"}

def reject_application(state: State) -> State:
    print("Rejecting the application...")
    return {**state, "response": "candidate rejected!"}

# ---- Define Routing Logic ---- #

def routing_function(state: State) -> str:
    level = state.get("experience_level", "")
    match = state.get("skill_match", "")
    if level == "entry level":
        return "schedule_hr_interview"
    elif level == "mid level":
        return "schedule_hr_interview" if match == "match" else "escalate_to_manager"
    elif level == "senior level":
        return "schedule_hr_interview" if match == "match" else "reject_application"
    return "reject_application"

# ---- Build the Graph ---- #

workflow.add_node("categorize_experience", categorize_experience)
workflow.add_node("assess_skill_match", assess_skill_match)
workflow.add_node("schedule_hr_interview", schedule_hr_interview)
workflow.add_node("escalate_to_manager", escalate_to_manager)
workflow.add_node("reject_application", reject_application)

workflow.set_entry_point("categorize_experience")
workflow.add_edge("categorize_experience", "assess_skill_match")

workflow.add_conditional_edges(
    "assess_skill_match",
    routing_function,
    {
        "schedule_hr_interview": "schedule_hr_interview",
        "escalate_to_manager": "escalate_to_manager",
        "reject_application": "reject_application"
    }
)

workflow.add_edge("schedule_hr_interview", END)
workflow.add_edge("escalate_to_manager", END)
workflow.add_edge("reject_application", END)

# Compile the workflow
graph = workflow.compile()



application_text = (
    "I have over 5 years of experience working as a backend Python developer. "
    "I've built scalable APIs using Django and Flask, managed cloud deployments on AWS, "
    "and led a small team of engineers. I'm currently looking for a senior Python developer role."
)
# Run the graph with the application
response = graph.invoke({
    "application": application_text,
    "experience_level": "",   # Leave blank to be inferred
    "skill_match": "",
    "job_title": "Python Developer",  # Optional
    "response": ""
})

# Output the final decision
print("Final decision:", response["response"])
