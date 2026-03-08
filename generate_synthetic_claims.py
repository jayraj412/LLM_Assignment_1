import csv
import json
import random

# Define lists of possible values for generating realistic claims
policy_types = ["Commercial Auto", "General Liability", "Commercial Property", "Workers Compensation", "Professional Liability"]
industries = ["Construction", "Retail", "Manufacturing", "IT Services", "Healthcare", "Hospitality"]

claims_scenarios = [
    {
        "incident": "Water pipe burst in the main office causing damage to computers, servers, and carpets. Operations halted for 3 days.",
        "policy": "Commercial Property",
        "underwriter_notes": "The physical damage to the computers, servers, and carpets is covered under the water damage provision. However, the claim for 3 days of business interruption is rejected because the policy carries a 72-hour waiting period deductible for business income coverage. Since the halt was exactly 3 days (72 hours), no business income loss is payable.",
        "rejected_parts": "Business Interruption (waiting period applies)",
        "accepted_parts": "Physical Property Damage"
    },
    {
        "incident": "A customer slipped on a wet floor in the retail store and broke their arm. They are suing for medical expenses and emotional distress.",
        "policy": "General Liability",
        "underwriter_notes": "Medical expenses are accepted under the Medical Payments to Others coverage. The claim for emotional distress is currently under reservation of rights, but typically general liability policies require bodily injury to trigger emotional distress damages. Since there is a bodily injury (broken arm), we will accept the defense of the suit, but any punitive damages awarded for negligence will be rejected as per the punitive damages exclusion.",
        "rejected_parts": "Punitive Damages (if awarded)",
        "accepted_parts": "Medical Expenses, Legal Defense Costs"
    },
    {
        "incident": "Employee suffered a repetitive stress injury (carpal tunnel) from typing and filed a claim for surgery and 6 weeks of lost wages.",
        "policy": "Workers Compensation",
        "underwriter_notes": "Carpal tunnel is recognized as an occupational disease. The surgery and related medical costs are accepted. However, the exact lost wages calculation must be adjusted. The employee claimed 100% of lost wages, but the statutory benefit is 66.67% of the Average Weekly Wage (AWW). The portion of the wage claim exceeding 66.67% is rejected.",
        "rejected_parts": "Lost wages exceeding statutory limit (33.33% of claimed wages)",
        "accepted_parts": "Medical Surgery Costs, 66.67% of Lost Wages"
    },
    {
        "incident": "Delivery van rear-ended a third-party vehicle. The third-party is claiming $15,000 in vehicle damage and $5,000 for a rented replacement vehicle. Our driver was not on the clock.",
        "policy": "Commercial Auto",
        "underwriter_notes": "The claim is entirely rejected. The investigation revealed the employee was using the company vehicle for personal errands outside of business hours without authorization, which falls under the non-permissive use exclusion in the commercial auto policy.",
        "rejected_parts": "Entire Claim (Vehicle Damage and Rental)",
        "accepted_parts": "None"
    },
    {
        "incident": "Software deployed by the insured company contained a bug that caused a client's e-commerce site to go down for 12 hours, resulting in $50,000 of lost sales.",
        "policy": "Professional Liability",
        "underwriter_notes": "The claim for negligent performance of professional services is covered. The loss of $50,000 is accepted. However, the client is also claiming $10,000 in 'reputational harm'. The policy explicitly excludes damages for reputational harm and loss of future market share. That $10,000 portion is rejected.",
        "rejected_parts": "Reputational Harm ($10,000)",
        "accepted_parts": "Direct Financial Loss from downtime ($50,000)"
    },
    {
        "incident": "Fire broke out in the manufacturing plant destroying raw materials and machinery. The insured is claiming the replacement cost of a 15-year-old machine as if it were brand new.",
        "policy": "Commercial Property",
        "underwriter_notes": "The raw materials are covered at actual cost. The machinery claim must be adjusted. The policy valuation clause for this specific 15-year-old machine is Actual Cash Value (ACV), not Replacement Cost (RC). Therefore, we must apply a 60% depreciation factor. The difference in cost between RC and ACV is rejected.",
        "rejected_parts": "Replacement Cost of machinery (depreciation applied)",
        "accepted_parts": "Actual Cash Value of machinery, Raw Materials"
    },
    {
        "incident": "A cyber attack encrypted company servers. The insured paid a $100,000 ransom and is claiming the ransom amount, plus $20,000 for IT forensics, and $5,000 for upgraded security software.",
        "policy": "Cyber Liability",  # Using a specific policy type here to add variety
        "underwriter_notes": "The $20,000 for IT forensics is covered under the incident response provision. The $100,000 ransom is covered under the cyber extortion insuring agreement, as they obtained prior written consent from us before paying. However, the $5,000 for upgraded security software is rejected because the policy covers restoring systems to their pre-breach state; betterment or upgrades are excluded.",
        "rejected_parts": "Upgraded Security Software ($5,000 betterment)",
        "accepted_parts": "Ransom Payment, IT Forensics"
    },
    {
        "incident": "A powerful storm blew the roof off the retail building. Rain destroyed inventory. The insured also claims the cost to remove a fallen tree from the empty parking lot.",
        "policy": "Commercial Property",
        "underwriter_notes": "Damage to the building and the interior wet inventory are covered perils. The tree removal is rejected. The policy has a debris removal extension, but it only applies if the debris caused damage to covered property or blocked access to the building. Since the tree was in an empty corner of the lot and didn't hit anything or block access, the cost to remove it is not covered.",
        "rejected_parts": "Tree removal from empty lot",
        "accepted_parts": "Roof repair, Inventory replacement"
    },
    {
        "incident": "An employee stole $25,000 from the company safe over a period of 6 months. The employer discovered it and fired the employee. They are claiming the lost cash and $5,000 for a private investigator.",
        "policy": "Commercial Crime",
        "underwriter_notes": "The employee theft of $25,000 is covered under the Employee Dishonesty insuring agreement. The $5,000 investigative cost is rejected. Our standard crime policy covers direct physical loss of money, but investigative expenses incurred by the insured to prove the loss are expressly excluded.",
        "rejected_parts": "Private Investigator Fees ($5,000)",
        "accepted_parts": "Stolen Cash ($25,000)"
    },
    {
        "incident": "Company vehicle was broken into while parked overnight at a hotel. Thieves stole a laptop and $5,000 worth of specialized tools left in the back seat.",
        "policy": "Commercial Auto",
        "underwriter_notes": "The broken window and damage to the vehicle are covered under Comprehensive auto coverage. The theft of the laptop and tools is rejected under the Auto policy. Personal property and tools in transit must be covered under an Inland Marine or Property off-premises endorsement, which this insured does not carry. Additionally, leaving tools visible in an unattended vehicle violates the minimum security condition of their property policy anyway.",
        "rejected_parts": "Laptop and Specialized Tools",
        "accepted_parts": "Vehicle Glass Damage"
    }
]

# Generate more synthetic combinations based on the core scenarios
all_claims = []
claim_id_counter = 1000

# Duplicating and slightly randomizing to get a decent sized list for testing RAG (e.g., 50 records)
for i in range(50):
    base_scenario = claims_scenarios[i % len(claims_scenarios)]
    
    claim = {
        "Claim_ID": f"CLM-{claim_id_counter}",
        "Industry": random.choice(industries),
        "Policy_Type": base_scenario["policy"],
        "Claim_Amount": f"${random.randint(5, 150) * 1000}",
        "Incident_Description": base_scenario["incident"],
        "Expert_Decision": "Partial Accept" if "rejected" in base_scenario["rejected_parts"].lower() or base_scenario["accepted_parts"] != "None" else "Reject",
        "Underwriter_Reasoning": base_scenario["underwriter_notes"],
        "Accepted_Parts": base_scenario["accepted_parts"],
        "Rejected_Parts": base_scenario["rejected_parts"]
    }
    
    # Fix the generic Expert Decision logic slightly
    if base_scenario["accepted_parts"] == "None":
        claim["Expert_Decision"] = "Full Reject"
    elif base_scenario["rejected_parts"] == "None" or base_scenario["rejected_parts"] == "":
        claim["Expert_Decision"] = "Full Accept"
    else:
        claim["Expert_Decision"] = "Partial Reject / Partial Accept"
        
    all_claims.append(claim)
    claim_id_counter += 1

# Write to CSV
file_path = "c:/Users/sunit/Desktop/LLM_Assignment/synthetic_underwriting_claims.csv"
with open(file_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=all_claims[0].keys())
    writer.writeheader()
    writer.writerows(all_claims)

# Also write to JSON for easier ingestion in some RAG setups
json_path = "c:/Users/sunit/Desktop/LLM_Assignment/synthetic_underwriting_claims.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(all_claims, f, indent=4)

print(f"Generated {len(all_claims)} synthetic claims and saved to {file_path} and {json_path}")
