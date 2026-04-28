import json
from datetime import datetime

def calculate_priority_score(ticket, account):
    score = 0
    
    
    priority_map = {"urgent": 30, "high": 20, "medium": 10, "low": 0}
    score += priority_map.get(ticket['priority'], 0)
    
    
    tier_map = {"enterprise": 20, "pro": 10, "basic": 0}
    score += tier_map.get(ticket['customer_tier'], 0)
    
    
    if account and account.get('health_score', 100) < 50:
        score += 15
        
    
    created_at = datetime.fromisoformat(ticket['created_at'].replace('Z', ''))
    days_old = (datetime(2026, 4, 28) - created_at).days
    score += min(days_old * 2, 20)  
    
    return score

def get_triage_list(tickets_path, accounts_path):
    with open(tickets_path) as f: tickets = json.load(f)
    with open(accounts_path) as f: accounts = {a['customer_name']: a for a in json.load(f)}
    
    ranked_tickets = []
    
    for t in tickets:
        if t['status'] != "resolved":
            account = accounts.get(t['customer_name'])
            t['total_score'] = calculate_priority_score(t, account)
            t['health_score'] = account['health_score'] if account else "N/A"
            ranked_tickets.append(t)
            
    
    return sorted(ranked_tickets, key=lambda x: x['total_score'], reverse=True)[:3]