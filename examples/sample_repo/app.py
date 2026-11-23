# FICTIONAL sample app used to test the PolicyLens code scanner.
import openai
import pandas as pd
from deepface import DeepFace

FEATURES = ["years_experience", "skills_match", "gender", "age"]


def rank_candidates(applicants: pd.DataFrame):
    scores = applicants[FEATURES].mean(axis=1)
    return applicants.assign(score=scores).sort_values("score", ascending=False)


def screen_resume(resume_text: str) -> str:
    resp = openai.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": resume_text}])
    return resp.choices[0].message.content


def process(applicant):
    mood = DeepFace.analyze(applicant["interview_video_frame"], actions=["emotion"])
    if applicant["score"] < 0.4:
        auto_reject(applicant)  # no recruiter involved
