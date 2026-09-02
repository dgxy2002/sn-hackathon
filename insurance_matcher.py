"""
Insurance Plan Matching Agent using LangGraph & AWS Bedrock
Matches users to insurance plans based on lifestyle and needs
"""

from typing import Annotated, TypedDict
import json
from langgraph.graph import StateGraph, START, END
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from dummy_data import get_user, get_all_plans, filter_plans_by_budget, filter_plans_by_coverage


# ============================================================================
# STATE DEFINITION
# ============================================================================
class MatchingState(TypedDict):
    """Shared state across the agent"""
    user_id: str
    user_profile: dict
    retrieved_plans: list
    ranked_results: list
    reasoning: str


# ============================================================================
# NODE FUNCTIONS
# ============================================================================
def retrieve_user_node(state: MatchingState) -> dict:
    """Node 1: Retrieve user profile from dummy data"""
    print(f"\n Retrieving user: {state['user_id']}")
    
    user = get_user(state['user_id'])
    if not user:
        raise ValueError(f"User {state['user_id']} not found")
    
    print(f"   ✓ User loaded: {user['name']}, Age {user['age']}")
    return {"user_profile": user}


def retrieve_candidate_plans_node(state: MatchingState) -> dict:
    """Node 2: Retrieve candidate plans from dummy database"""
    print("\n Retrieving candidate plans...")
    
    user = state["user_profile"]
    all_plans = get_all_plans()
    
    # Filter by budget
    candidate_plans = filter_plans_by_budget(all_plans, user["budget_monthly"] * 1.2)  # 20% flexibility
    print(f"   ✓ Plans within budget: {len(candidate_plans)}")
    
    # Filter by coverage needs (normalize to lowercase underscore format)
    required_coverage = [need.lower().replace(" ", "_") for need in user["coverage_needs"]]
    candidate_plans = filter_plans_by_coverage(candidate_plans, required_coverage)
    print(f"   ✓ Plans with required coverage: {len(candidate_plans)}")
    
    return {"retrieved_plans": candidate_plans}


def match_plans_with_bedrock_node(state: MatchingState) -> dict:
    """Node 3: Use Bedrock/Claude to intelligently rank and match plans"""
    print("\n Analyzing matches with Bedrock...")
    
    user = state["user_profile"]
    plans = state["retrieved_plans"]
    
    if not plans:
        return {
            "ranked_results": [],
            "reasoning": "No plans match the user's budget and coverage requirements."
        }
    
    # Format plans for Claude
    plans_text = "\n\n".join([
        f"Plan: {p['name']} ({p['plan_id']})\n"
        f"  Provider: {p['provider']}\n"
        f"  Monthly: ${p['monthly_premium']} | Deductible: ${p['deductible']} | OOP Max: ${p['out_of_pocket_max']}\n"
        f"  Coverage: {', '.join([k for k, v in p['coverage'].items() if v])}\n"
        f"  Best for: {', '.join(p['best_for'])}\n"
        f"  Description: {p['description']}"
        for p in plans
    ])
    
    prompt = f"""You are an expert insurance advisor. Analyze this user's profile and match them to the best insurance plans.

USER PROFILE:
- Name: {user['name']}
- Age: {user['age']}
- Lifestyle: {', '.join(user['lifestyle'])}
- Monthly Budget: ${user['budget_monthly']}
- Health Status: {user['health_status']}
- Employment: {user['employment_type']}
- Family Status: {user['family_status']}
- Pre-existing Conditions: {user['pre_existing_conditions'] or 'None'}
- Coverage Needs: {', '.join(user['coverage_needs'])}

AVAILABLE PLANS:
{plans_text}

For each plan, provide:
1. Match Score (0-100): How well does it fit THIS specific user?
2. Why This Fits: Explain why this plan matches their lifestyle
3. Key Strengths: 2-3 benefits most valuable to them
4. Potential Drawbacks: Any limitations for them

Rank the plans by best fit (highest score first).

Format your response as JSON with this structure:
{{
  "ranked_plans": [
    {{
      "plan_id": "plan_001",
      "name": "Plan Name",
      "score": 95,
      "fit_reason": "explanation",
      "strengths": ["strength1", "strength2"],
      "drawbacks": ["drawback1"],
      "recommendation": "Why this is a good choice"
    }}
  ],
  "top_recommendation": "plan_id",
  "general_advice": "Overall recommendation text"
}}"""

    # Call Bedrock using working inference profile ID
    client = ChatBedrock(
        model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        region_name="us-east-1",
        model_kwargs={
            "max_tokens": 2500,
            "temperature": 0.2
        }
    )
    
    try:
        response = client.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        # Extract JSON from response
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # Map back to full plan objects
                ranked_results = []
                for ranked_plan in result.get("ranked_plans", []):
                    plan_id = ranked_plan["plan_id"]
                    full_plan = next((p for p in plans if p["plan_id"] == plan_id), None)
                    if full_plan:
                        full_plan["match_score"] = ranked_plan["score"]
                        full_plan["fit_reason"] = ranked_plan["fit_reason"]
                        full_plan["strengths"] = ranked_plan["strengths"]
                        full_plan["drawbacks"] = ranked_plan["drawbacks"]
                        full_plan["recommendation"] = ranked_plan["recommendation"]
                        ranked_results.append(full_plan)
                
                reasoning = result.get("general_advice", "")
                print(f"   ✓ Bedrock analysis complete: {len(ranked_results)} plans ranked")
                
                return {
                    "ranked_results": ranked_results,
                    "reasoning": reasoning
                }
        except json.JSONDecodeError:
            print("   ⚠ Could not parse JSON, using raw response")
            return {
                "ranked_results": plans,
                "reasoning": response_text
            }
    except Exception as e:
        print(f"   ⚠ Bedrock call failed: {str(e)}")
        print("   → Returning unranked plans as fallback")
        return {
            "ranked_results": plans,
            "reasoning": f"Bedrock matching failed: {str(e)}. Returning unranked plans."
        }


# ============================================================================
# BUILD THE GRAPH
# ============================================================================
def build_matching_graph():
    """Construct the LangGraph workflow"""
    builder = StateGraph(MatchingState)
    
    # Add nodes
    builder.add_node("retrieve_user", retrieve_user_node)
    builder.add_node("retrieve_plans", retrieve_candidate_plans_node)
    builder.add_node("match_plans", match_plans_with_bedrock_node)
    
    # Add edges (workflow)
    builder.add_edge(START, "retrieve_user")
    builder.add_edge("retrieve_user", "retrieve_plans")
    builder.add_edge("retrieve_plans", "match_plans")
    builder.add_edge("match_plans", END)
    
    return builder.compile()


# ============================================================================
# RUN THE AGENT
# ============================================================================
def run_matching_agent(user_id: str):
    """Execute the matching agent for a user"""
    print("=" * 70)
    print(f" Insurance Plan Matching Agent")
    print("=" * 70)
    
    graph = build_matching_graph()
    
    # Initial state
    initial_state = {
        "user_id": user_id,
        "user_profile": {},
        "retrieved_plans": [],
        "ranked_results": [],
        "reasoning": ""
    }
    
    # Run the agent
    result = graph.invoke(initial_state)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 MATCHING RESULTS")
    print("=" * 70)
    
    user = result["user_profile"]
    print(f"\n👤 {user['name']} (Age {user['age']}, Budget: ${user['budget_monthly']}/mo)")
    print(f"   Lifestyle: {', '.join(user['lifestyle'])}")
    print(f"   Coverage Needs: {', '.join(user['coverage_needs'])}")
    
    print(f"\n💡 General Advice:")
    print(f"   {result['reasoning']}")
    
    if result["ranked_results"]:
        print(f"\n🎯 Top Plan Recommendations:")
        for i, plan in enumerate(result["ranked_results"][:3], 1):
            print(f"\n   {i}. {plan['name']} (Score: {plan.get('match_score', 'N/A')}/100)")
            print(f"      Provider: {plan['provider']}")
            print(f"      Monthly: ${plan['monthly_premium']} | Deductible: ${plan['deductible']}")
            print(f"      Why it fits: {plan.get('fit_reason', 'Matches your needs')}")
            if "strengths" in plan:
                print(f"      Strengths: {', '.join(plan['strengths'])}")
            if "drawbacks" in plan:
                print(f"      Drawbacks: {', '.join(plan['drawbacks'])}")
    else:
        print("\n⚠️  No suitable plans found within your budget and coverage requirements.")
    
    print("\n" + "=" * 70)
    return result


if __name__ == "__main__":
    # Test with different users
    test_users = ["user_001", "user_002", "user_003", "user_004"]
    
    for user_id in test_users:
        run_matching_agent(user_id)
        print("\n\n")