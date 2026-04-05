import os
import json
import time
from typing import List
import openai
from openai import OpenAI

from src.scrapers.base import Job
from src.utils.logger import get_logger

logger = get_logger()

class LLMEvaluator:
    def __init__(self, config: dict):
        self.config = config
        self.llm_config = config.get('scoring', {}).get('llm_evaluator', {})
        self.enabled = self.llm_config.get('enabled', False)
        
        self.model = self.llm_config.get('model', 'meta/llama-3.1-70b-instruct')
        self.candidate_profile = self.llm_config.get('candidate_profile', '')
        
        api_key = os.getenv("NVIDIA_API_KEY")
        if self.enabled and not api_key:
            logger.error("NVIDIA_API_KEY is missing! LLM Evaluator disabled.")
            self.enabled = False
        
        if self.enabled:
            # NVIDIA API endpoint setup
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=api_key
            )
            logger.info(f"🤖 LLM Evaluator initialized using model: {self.model}")
            
    def evaluate_jobs(self, jobs: List[Job]) -> List[Job]:
        if not self.enabled or not jobs:
            return jobs
            
        top_k = self.llm_config.get('top_k_to_evaluate', 50)
        # Grab the top jobs first
        top_jobs = jobs[:top_k]
        
        # Then filter down to ONLY the ones that haven't been evaluated yet
        jobs_to_evaluate = [job for job in top_jobs if job.llm_score is None]
        
        if not jobs_to_evaluate:
            logger.info("All top jobs already have LLM scores. Skipping API calls.")
            return jobs
            
        logger.info(f"🧠 Prompting LLM to evaluate {len(jobs_to_evaluate)} jobs from top {len(top_jobs)}...")
        
        for idx, job in enumerate(jobs_to_evaluate):
            score, reasoning = self._evaluate_single_job(job)
            if score is not None:
                job.llm_score = score
                job.llm_reasoning = reasoning
                
                # Recalculate total score
                weights = self.config.get('scoring', {}).get('weights', {})
                w_money = weights.get('money', 0.15)
                w_passion = weights.get('passion', 0.25)
                w_location = weights.get('location', 0.20)
                w_llm = weights.get('llm', 0.40)
                
                job.total_score = (
                    w_money * job.money_score +
                    w_passion * job.passion_score +
                    w_location * job.location_score +
                    w_llm * job.llm_score
                )
            
            if (idx + 1) % 10 == 0:
                logger.info(f"   Evaluated {idx + 1}/{len(jobs_to_evaluate)} jobs...")
            
            # Base rate limit throttle
            time.sleep(1.5)
                
        # Re-sort
        jobs.sort(key=lambda x: x.total_score, reverse=True)
        return jobs

    def _evaluate_single_job(self, job: Job, max_retries=3):
        for attempt in range(max_retries):
            try:
                prompt = f"""
You are an expert technical recruiter matching a candidate with jobs.
Evaluate the following job against the candidate's profile and criteria.

### CANDIDATE PROFILE & CRITERIA:
{self.candidate_profile}

### JOB DETAILS:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description: {job.description if job.description else "No description provided."}

Output your evaluation strictly in valid JSON format with exactly these two keys:
"score": A float between 0 and 10 representing the fit.
"reasoning": A 1-sentence explanation of why it is a good or bad fit.

Do not include any markdown fences or extra text, just the raw JSON object.
"""
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2, # Low temp for consistency
                    max_tokens=150
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean up potential markdown formatting (```json ... ```)
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                data = json.loads(content)
                
                score = float(data.get("score", 0.0))
                reasoning = str(data.get("reasoning", "No reasoning provided."))
                
                # Clamp the score
                score = max(0.0, min(10.0, score))
                
                return score, reasoning
                
            except openai.RateLimitError:
                wait_time = (2 ** attempt) * 5
                logger.warning(f"Rate limit hit for {job.title}, sleeping {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            except Exception as e:
                logger.error(f"Failed to evaluate job {job.title} with LLM: {e}")
                return None, None
                
        return None, None
