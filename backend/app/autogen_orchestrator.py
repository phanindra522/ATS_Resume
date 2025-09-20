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
from typing import Dict, Any, Optional
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
    
    async def orchestrate_analysis(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """
        Orchestrate multi-agent analysis using AutoGen with caching integration.
        
        Args:
            resume_content: The resume text content
            job_description: The job description text
            
        Returns:
            Comprehensive analysis result with agent insights and final score
        """
        
        try:
            # Simple cache check using content hash
            cache_key = f"autogen_{abs(hash(resume_content + job_description))}"
            
            # Try to get from simple cache first
            try:
                cached_result = await self.cache_service.cache_service.get(
                    namespace="autogen_results",
                    identifier=cache_key,
                    cache_version="v1"
                )
                
                if cached_result:
                    return {
                        "status": "success",
                        "cached": True,
                        "result": cached_result,
                        "timestamp": cached_result.get("timestamp")
                    }
            except Exception:
                # Cache miss or error - continue with analysis
                pass
            
            # Create analysis prompt
            analysis_prompt = f"""
            Please analyze this resume against the job description using multi-agent coordination:

            **Job Description:**
            {job_description}

            **Resume Content:**
            {resume_content}

            Each agent should provide:
            1. Detailed analysis in your specialty area
            2. Numerical score (0-100) with justification
            3. Key strengths and gaps identified
            4. Specific recommendations for improvement

            Final coordinator should synthesize all agent feedback into overall score and summary.
            """
            
            # Setup group chat with all agents
            agents_list = [
                self.user_proxy,
                self.keyword_agent,
                self.skill_agent, 
                self.experience_agent,
                self.education_agent,
                self.semantic_agent,
                self.coordinator_agent
            ]
            
            group_chat = GroupChat(
                agents=agents_list,
                messages=[],
                max_round=10,
                speaker_selection_method="round_robin"
            )
            
            manager = GroupChatManager(
                groupchat=group_chat,
                llm_config={"config_list": self.config_list}
            )
            
            # Execute orchestration
            chat_result = self.user_proxy.initiate_chat(
                manager,
                message=analysis_prompt
            )
            
            # Parse results from chat history
            analysis_result = self._parse_chat_results(chat_result)
            
            # Cache the result
            try:
                await self.cache_service.cache_service.set(
                    namespace="autogen_results",
                    identifier=cache_key,
                    data=analysis_result,
                    ttl_seconds=3600,  # 1 hour cache
                    cache_version="v1"
                )
            except Exception:
                # Cache storage failed but continue
                pass
            
            return {
                "status": "success", 
                "cached": False,
                "result": analysis_result,
                "chat_history": chat_result.chat_history if hasattr(chat_result, 'chat_history') else []
            }
            
        except Exception as e:
            # Fallback to direct agent analysis
            print(f"AutoGen orchestration failed: {e}")
            return await self._fallback_analysis(resume_content, job_description)
    
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
    
    async def _fallback_analysis(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """Fallback to direct agent analysis if AutoGen fails."""
        
        try:
            # Use existing agents directly
            keyword_result = await self.keyword_agent_obj.analyze(resume_content, job_description)
            skill_result = await self.skill_agent_obj.analyze(resume_content, job_description)
            experience_result = await self.experience_agent_obj.analyze(resume_content, job_description)
            education_result = await self.education_agent_obj.analyze(resume_content, job_description)
            semantic_result = await self.semantic_agent_obj.analyze(resume_content, job_description)
            
            # Calculate average score
            scores = [
                keyword_result.get("score", 0),
                skill_result.get("score", 0),
                experience_result.get("score", 0),
                education_result.get("score", 0),
                semantic_result.get("score", 0)
            ]
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            return {
                "status": "success_fallback",
                "cached": False,
                "result": {
                    "agent_analyses": {
                        "KeywordAgent": keyword_result,
                        "SkillAgent": skill_result,
                        "ExperienceAgent": experience_result,
                        "EducationAgent": education_result,
                        "SemanticAgent": semantic_result
                    },
                    "final_score": round(avg_score, 2),
                    "summary": "Direct agent analysis (AutoGen fallback)",
                    "fallback_used": True
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
