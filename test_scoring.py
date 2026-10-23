from app.scoring import score_offer

profile = {"competences": ["Python", "SQL"], "experiences": []}
offer = {"title": "Data Analyst", "company": "Test", "location": "Remote", "description": "Python, SQL, dashboards"}
print(score_offer(profile, offer))
