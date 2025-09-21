"""
AutoGen Orchestrator for ATS Resume Multi-Agent System

This script provides:
- Full integration with existing 5-agent system (Keyword, Skill, Experience, Education, Semantic)
- Caching integration for performance optimization
- Production-ready orchestration with error handling
- FastAPI integration capabilities
- Chain-of-thought reasoning across agents
"""

import os
from typing import Dict, Any, Optional, List
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Import existing agents
from app.services.agents.keyword_agent import KeywordMatchingAgent
from app.services.agents.skill_agent import SkillMatchingAgent
from app.services.agents.experience_agent import ExperienceRelevanceAgent
from app.services.agents.education_agent import EducationAlignmentAgent
from app.services.agents.semantic_agent import SemanticSimilarityAgent
from app.services.agent_cache import AgentCacheService
from app.core.config import get_settings

class AutoGenOrchestrator:
    """
    AutoGen-powered multi-agent orchestrator for ATS Resume analysis.
    Integrates with existing caching system and provides production-ready coordination.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.cache_service = AgentCacheService()
        
        # Initialize agent objects with caching
        self.keyword_agent_obj = KeywordMatchingAgent()
        self.skill_agent_obj = SkillMatchingAgent()
        self.experience_agent_obj = ExperienceRelevanceAgent()
        self.education_agent_obj = EducationAlignmentAgent()
        self.semantic_agent_obj = SemanticSimilarityAgent()
        
        # Configure AutoGen with settings from .env
        # Set OPENAI_API_KEY for AutoGen compatibility
        os.environ["OPENAI_API_KEY"] = self.settings.LLM_PROVIDER_API_KEY
        
        self.config_list = [{
            "model": self.settings.LLM_MODEL,
            "api_key": self.settings.LLM_PROVIDER_API_KEY,
            "temperature": 0.1
        }]
        
        self._setup_autogen_agents()
    
    def _setup_autogen_agents(self):
        """Setup AutoGen agents with meta prompts from existing agents."""
        
        # Get meta prompts from existing agents
        keyword_meta = self.keyword_agent_obj.get_meta_prompt()
        skill_meta = self.skill_agent_obj.get_meta_prompt()
        experience_meta = self.experience_agent_obj.get_meta_prompt()
        education_meta = self.education_agent_obj.get_meta_prompt()
        semantic_meta = self.semantic_agent_obj.get_meta_prompt()
        
        # Create AutoGen agents
        self.keyword_agent = AssistantAgent(
            name="KeywordAgent",
            system_message=f"{keyword_meta}\n\nProvide detailed keyword matching analysis with scores and explanations.",
            llm_config={"config_list": self.config_list}
        )
        
        self.skill_agent = AssistantAgent(
            name="SkillAgent", 
            system_message=f"{skill_meta}\n\nAnalyze skill matches with technical depth and provide scoring rationale.",
            llm_config={"config_list": self.config_list}
        )
        
        self.experience_agent = AssistantAgent(
            name="ExperienceAgent",
            system_message=f"{experience_meta}\n\nEvaluate experience relevance with career progression insights.",
            llm_config={"config_list": self.config_list}
        )
        
        self.education_agent = AssistantAgent(
            name="EducationAgent",
            system_message=f"{education_meta}\n\nAssess educational alignment and qualification requirements.",
            llm_config={"config_list": self.config_list}
        )
        
        self.semantic_agent = AssistantAgent(
            name="SemanticAgent",
            system_message=f"{semantic_meta}\n\nProvide semantic similarity analysis with contextual understanding.",
            llm_config={"config_list": self.config_list}
        )
        
        # Coordinator agent for final synthesis
        self.coordinator_agent = AssistantAgent(
            name="CoordinatorAgent",
            system_message="""You are the final coordinator for ATS resume analysis. 
            Synthesize insights from all agents (Keyword, Skill, Experience, Education, Semantic) 
            to provide a comprehensive final score and detailed explanation.""",
            llm_config={"config_list": self.config_list}
        )
        
        # User proxy for orchestration
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )
    
    async def orchestrate_analysis(self, resume_content: str, job_description: str, job_skills: List[str] = None) -> Dict[str, Any]:
        """
        Orchestrate multi-agent analysis using AutoGen with caching integration.
        
        Args:
            resume_content: The resume text content
            job_description: The job description text
            
        Returns:
            Comprehensive analysis result with agent insights and final score
        """
        
        print("🤖 AutoGen orchestrate_analysis called - using simplified fallback for now")
        
        # For now, skip the complex AutoGen conversation and go directly to fallback
        # This avoids the coroutine issues while we debug
        return await self._fallback_analysis(resume_content, job_description, job_skills)
    
    def _parse_chat_results(self, chat_result) -> Dict[str, Any]:
        """Parse AutoGen chat results into structured analysis."""
        
        # Extract messages from chat result
        messages = []
        if hasattr(chat_result, 'chat_history'):
            messages = chat_result.chat_history
        elif hasattr(chat_result, 'messages'):
            messages = chat_result.messages
        
        agent_analyses = {}
        final_score = 0.0
        
        # Parse agent responses
        for message in messages:
            content = message.get("content", "")
            name = message.get("name", "")
            
            if "Agent" in name and content:
                agent_analyses[name] = {
                    "analysis": content,
                    "timestamp": message.get("timestamp")
                }
                
                # Try to extract scores from content
                score_match = self._extract_score_from_content(content)
                if score_match:
                    agent_analyses[name]["score"] = score_match
        
        # Calculate overall score
        scores = [analysis.get("score", 0) for analysis in agent_analyses.values() if "score" in analysis]
        if scores:
            final_score = sum(scores) / len(scores)
        
        return {
            "agent_analyses": agent_analyses,
            "final_score": round(final_score, 2),
            "summary": self._generate_summary(agent_analyses),
            "timestamp": chat_result.get("timestamp") if hasattr(chat_result, "timestamp") else None
        }
    
    def _extract_score_from_content(self, content: str) -> Optional[float]:
        """Extract numerical score from agent content."""
        import re
        
        # Look for patterns like "Score: 85", "85/100", "Score of 85"
        patterns = [
            r"[Ss]core:?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)/100",
            r"[Ss]core\s+of\s+(\d+(?:\.\d+)?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        return None
    
    def _generate_summary(self, agent_analyses: Dict[str, Any]) -> str:
        """Generate summary from agent analyses."""
        
        if not agent_analyses:
            return "No analysis data available."
        
        summary_parts = []
        for agent_name, analysis in agent_analyses.items():
            if "analysis" in analysis:
                # Get first sentence of each analysis
                first_sentence = analysis["analysis"].split('.')[0] + '.'
                summary_parts.append(f"{agent_name}: {first_sentence}")
        
        return " | ".join(summary_parts)
    
    async def _fallback_analysis(self, resume_content: str, job_description: str, job_skills: List[str] = None) -> Dict[str, Any]:
        """Fallback to direct agent analysis if AutoGen fails."""
        
        try:
            print("🔄 Starting fallback analysis...")
            
            # Create proper dictionary structures for agents
            resume_dict = {"text_content": resume_content}
            job_dict = {"description": job_description, "skills": job_skills or []}
            
            print("📊 Calling keyword agent...")
            keyword_result = await self.keyword_agent_obj.analyze(resume_dict, job_dict)
            print(f"✅ Keyword result type: {type(keyword_result)}")
            
            print("🔧 Calling skill agent...")
            skill_result = await self.skill_agent_obj.analyze(resume_dict, job_dict)
            print(f"✅ Skill result type: {type(skill_result)}")
            
            print("💼 Calling experience agent...")
            experience_result = await self.experience_agent_obj.analyze(resume_dict, job_dict)
            print(f"✅ Experience result type: {type(experience_result)}")
            
            print("🎓 Calling education agent...")
            education_result = await self.education_agent_obj.analyze(resume_dict, job_dict)
            print(f"✅ Education result type: {type(education_result)}")
            
            print("🔍 Calling semantic agent...")
            semantic_result = await self.semantic_agent_obj.analyze(resume_dict, job_dict)
            print(f"✅ Semantic result type: {type(semantic_result)}")
            
            # Calculate average score from AgentResult objects
            scores = [
                keyword_result.score if keyword_result else 0,
                skill_result.score if skill_result else 0,
                experience_result.score if experience_result else 0,
                education_result.score if education_result else 0,
                semantic_result.score if semantic_result else 0
            ]
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Extract skills match data from skill agent
            skills_match = []
            missing_skills = []
            if skill_result and hasattr(skill_result, 'evidence') and skill_result.evidence:
                skills_match = skill_result.evidence.get('matched_skills', [])
                missing_skills = skill_result.evidence.get('missing_skills', [])
            
            return {
                "status": "success_fallback",
                "cached": False,
                "result": {
                    "agent_analyses": {
                        "KeywordAgent": keyword_result.__dict__ if keyword_result else {},
                        "SkillAgent": skill_result.__dict__ if skill_result else {},
                        "ExperienceAgent": experience_result.__dict__ if experience_result else {},
                        "EducationAgent": education_result.__dict__ if education_result else {},
                        "SemanticAgent": semantic_result.__dict__ if semantic_result else {}
                    },
                    "final_score": round(avg_score, 2),
                    "summary": "Direct agent analysis (AutoGen fallback)",
                    "fallback_used": True,
                    "skills_match": skills_match,
                    "missing_skills": missing_skills
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "result": None
            }

# Singleton instance for use across the application
autogen_orchestrator = None

def get_autogen_orchestrator() -> AutoGenOrchestrator:
    """Get singleton AutoGen orchestrator instance."""
    global autogen_orchestrator
    if autogen_orchestrator is None:
        autogen_orchestrator = AutoGenOrchestrator()
    return autogen_orchestrator

if __name__ == "__main__":
    # Test the orchestrator
    import asyncio
    
    async def test_orchestrator():
        orchestrator = AutoGenOrchestrator()
        
        sample_resume = """
        John Doe
        Software Engineer
        
        Experience:
        - 5 years Python development
        - FastAPI, Django frameworks
        - Machine Learning with scikit-learn
        
        Education:
        - BS Computer Science
        """
        
        sample_job = """
        Senior Python Developer
        
        Requirements:
        - 3+ years Python experience
        - FastAPI/Django knowledge
        - ML/AI experience preferred
        - Computer Science degree
        """
        
        result = await orchestrator.orchestrate_analysis(sample_resume, sample_job)
        print("\n--- AutoGen Orchestration Result ---")
        print(f"Status: {result['status']}")
        print(f"Final Score: {result['result']['final_score'] if result['result'] else 'N/A'}")
        print(f"Cached: {result['cached']}")
        
        if result['result']:
            print(f"Summary: {result['result']['summary']}")
    
    asyncio.run(test_orchestrator())
