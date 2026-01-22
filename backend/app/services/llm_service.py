import httpx
import json
import re
import asyncio
from app.core.config import settings

class LLMOrchestrator:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL

    async def _call_agent(self, agent_name: str, model: str, system_prompt: str, user_prompt: str):
        print(f"--- [AGENT: {agent_name}] is thinking using {model}... ---")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "keep_alive": 0, 
            "options": {"num_ctx": 4096, "temperature": 0.1, "num_predict": 1500}
        }
        try:
            async with httpx.AsyncClient(timeout=400.0) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)
                raw = response.json()['choices'][0]['message']['content']
                
                # REPAIR: Remove DeepSeek <think> tags and clean JSON
                processed = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL)
                processed = processed.replace('`', '"').replace('\n', ' ').replace('\r', ' ')
                
                start, end = processed.find('{'), processed.rfind('}')
                if start == -1 or end == -1: return {"error": "No JSON found"}
                
                return json.loads(processed[start:end+1], strict=False)
        except Exception as e:
            return {"error": str(e)}

    async def interpret_user_prompt(self, raw_prompt: str):
        """AGENT 0: Extracts brief + identifies what the user ALREADY has"""
        sys = "You are a Senior Marketing Analyst. Extract the brief and note any existing assets mentioned."
        user = f"Chat: {raw_prompt}. Return JSON: {{'icp_profile','pain_points','brand_voice','offer_type','conversion_goal', 'existing_topics': 'list of assets the user already has'}}"
        return await self._call_agent("INTAKE", "llama3", sys, user)

    async def get_strategy_and_theme(self, icp, pain, offer, goal, existing_topics="None"):
        """AGENT 1: Director - Now with dynamic scoring and uniqueness check"""
        sys = "You are a High-End UX Director. You are CRITICAL. You ONLY speak in JSON."
        user = f"""
        Analyze project: {icp} | {pain}. 
        Existing Assets to Avoid: {existing_topics}.
        
        SCORING RULES: 
        - conversion_score: Give a REALISTIC percentage (70-98). 
        - Lower the score if the niche is crowded or the pain point is vague.
        
        Return ONLY JSON: {{
            "title": "catchy unique title", 
            "type": "Calculator, Checklist, or Report",
            "conversion_score": random_integer_based_on_complexity,
            "primary_hex": "muted hex",
            "bg_keyword": "room interior", "image_keyword": "object",
            "li_image_keyword": "success scene"
        }}
        """
        return await self._call_agent("DIRECTOR", "llama3", sys, user)

    async def build_funnel_and_asset(self, title, icp, type, voice, goal, url):
        """AGENT 2: Mastermind (DeepSeek R1) - Full Logic & Copywriting"""
        sys = f"You are a Senior Copywriter & Logic Engineer. Voice: {voice}. Goal: {goal}. ONLY JSON."
        user = f"""
        Build funnel assets for '{title}' targeting {icp}.
        
        1. PAS COPY: Write a PAS Headline (max 8 words), an Agitation paragraph (30 words), and 3 Feature solutions.
        2. SOCIAL: Write a 150-word LinkedIn story. Include link: {url}.
        3. NURTURE: Write 3 emails. 
        4. ASSET LOGIC: 
           - IF '{type}' is Calculator: {{'input_label','multiplier','unit','result_label'}}.
           - IF '{type}' is Checklist: {{'tips': ['tip1','tip2','tip3']}}.
           - IF '{type}' is Report: {{'summary', 'data_points': [{{'label','value'}}]}}.
        
        Return ONLY JSON: {{
            "headline", "sub", "agitation", "features": [], "why_us", 
            "linkedin_post", "upgrade_offer_copy", "emails": [{{'subject','body'}}], 
            "asset_logic": {{}} 
        }}
        """
        return await self._call_agent("MASTERMIND", "deepseek-r1:latest", sys, user)

engine = LLMOrchestrator()