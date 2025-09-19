"""
AutoGen Orchestrator Example for ATS Resume Agents

This script demonstrates:
- Agent collaboration (Skill and Experience agents)
- Meta-prompting using chain-of-thought
- Fallback handling if LLM does not respond
"""

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from app.services.agents.keyword_agent import KeywordMatchingAgent
from app.services.agents.skill_agent import SkillMatchingAgent
from app.services.agents.experience_agent import ExperienceRelevanceAgent
from app.services.agents.education_agent import EducationAlignmentAgent

# Instantiate your agent classes to get their meta prompts
keyword_agent_obj = KeywordMatchingAgent()
skill_agent_obj = SkillMatchingAgent()
experience_agent_obj = ExperienceRelevanceAgent()
education_agent_obj = EducationAlignmentAgent()

# Get chain-of-thought meta prompts from each agent
keyword_meta_prompt = keyword_agent_obj.get_meta_prompt()
skill_meta_prompt = skill_agent_obj.get_meta_prompt()
experience_meta_prompt = experience_agent_obj.get_meta_prompt()
education_meta_prompt = education_agent_obj.get_meta_prompt()

# Define AutoGen agents for orchestration
keyword_agent = AssistantAgent(
    name="KeywordAgent",
    system_message=keyword_meta_prompt,
)
skill_agent = AssistantAgent(
    name="SkillAgent",
    system_message=skill_meta_prompt,
)
experience_agent = AssistantAgent(
    name="ExperienceAgent",
    system_message=experience_meta_prompt,
)
education_agent = AssistantAgent(
    name="EducationAgent",
    system_message=education_meta_prompt,
)
user_proxy = UserProxyAgent(name="UserProxy")

# Group chat setup for collaborative analysis
group_chat = GroupChat(
    agents=[user_proxy, keyword_agent, skill_agent, experience_agent, education_agent],
    messages=[{"role": "user", "content": "Analyze this resume and job description for keywords, skills, experience, and education alignment. Use chain-of-thought meta prompting and fallback to rule-based extraction if LLM does not respond."}],
)
manager = GroupChatManager(group_chat=group_chat)

if __name__ == "__main__":
    # Start the group chat orchestration
    result = manager.run()
    print("\n--- AutoGen Orchestration Result ---\n")
    print(result)
    print("\nIf LLM does not respond, fallback to rule-based extraction.")
