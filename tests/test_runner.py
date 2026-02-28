import time
import random
from datetime import datetime
import json
import os

from app.bot import PatientSimulatorBot
from scenarios.patient_scenarios import ScenarioManager

def run_test_suite(num_calls: int = 10):
    """
    Run multiple test calls
    """
    print(f"\n{'='*50}")
    print(f"Starting test suite with {num_calls} calls")
    print(f"{'='*50}\n")
    
    results = []
    
    for i in range(num_calls):
        # Get random scenario
        test_scenario = ScenarioManager.get_random_scenario()
        
        print(f"\n--- Test Call {i+1}/{num_calls} ---")
        print(f"Scenario: {test_scenario['name']}")
        print(f"Opening: {test_scenario['opening_line']}")
        
        # Initialize bot
        bot = PatientSimulatorBot(scenario_type=test_scenario['type'])
        
        try:
            # Make call to the test number
            call_sid = bot.start_call('+18054398008')
            print(f"Call initiated: {call_sid}")
            
            # Wait for call to complete (3-5 minutes)
            call_duration = random.randint(180, 300)
            print(f"Call in progress (approx {call_duration//60} minutes)...")
            
            # Simulate waiting
            for remaining in range(call_duration, 0, -60):
                if remaining > 0:
                    print(f"  {remaining//60} minutes remaining...")
                    time.sleep(60)  # Wait 1 minute between updates
            
            # Save results
            summary = bot.get_summary()
            results.append({
                'call_number': i+1,
                'scenario': test_scenario['type'],
                'call_sid': call_sid,
                'bugs_found': len(bot.bugs_found),
                'bug_details': bot.bugs_found,
                'duration_minutes': summary['duration_minutes'],
                'estimated_cost': summary['estimated_cost'],
                'transcript_file': bot.save_conversation()
            })
            
            print(f"Call completed. Bugs found: {len(bot.bugs_found)}")
            
        except Exception as e:
            print(f"Error in call: {e}")
            results.append({
                'call_number': i+1,
                'scenario': test_scenario['type'],
                'error': str(e)
            })
        
        # Random delay between calls
        if i < num_calls - 1:
            delay = random.randint(60, 180)
            print(f"Waiting {delay//60} minutes before next call...")
            time.sleep(delay)
    
    # Generate reports
    generate_test_report(results)
    generate_bug_report(results)
    
    print(f"\n{'='*50}")
    print("Test suite completed!")
    print(f"{'='*50}")

def generate_test_report(results: list):
    """Generate test execution report"""
    successful_calls = [r for r in results if 'error' not in r]
    
    report = {
        'summary': {
            'total_calls': len(results),
            'successful_calls': len(successful_calls),
            'failed_calls': len(results) - len(successful_calls),
            'total_bugs_found': sum(r.get('bugs_found', 0) for r in successful_calls),
            'scenarios_tested': list(set(r['scenario'] for r in successful_calls)),
            'total_cost': sum(r.get('estimated_cost', 0) for r in successful_calls)
        },
        'call_details': results,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save report
    filename = f"transcripts/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved: {filename}")
    return report

def generate_bug_report(results: list):
    """Generate detailed bug report"""
    
    # Collect all bugs
    all_bugs = []
    for result in results:
        if 'bug_details' in result:
            for bug in result['bug_details']:
                bug['scenario'] = result['scenario']
                bug['call_number'] = result['call_number']
                all_bugs.append(bug)
    
    # Organize by type
    bugs_by_type = {}
    for bug in all_bugs:
        bug_type = bug['type']
        if bug_type not in bugs_by_type:
            bugs_by_type[bug_type] = []
        bugs_by_type[bug_type].append(bug)
    
    # Generate report
    bug_report = {
        'summary': {
            'total_bugs': len(all_bugs),
            'unique_bug_types': len(bugs_by_type),
            'bugs_by_type': {k: len(v) for k, v in bugs_by_type.items()}
        },
        'bugs_by_type': bugs_by_type,
        'all_bugs': all_bugs,
        'recommendations': generate_recommendations(bugs_by_type),
        'timestamp': datetime.now().isoformat()
    }
    
    # Save bug report
    filename = f"transcripts/bug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(bug_report, f, indent=2)
    
    print(f"Bug report saved: {filename}")

def generate_recommendations(bugs_by_type: dict) -> list:
    """Generate recommendations based on bugs found"""
    recommendations = []
    
    if 'hallucination' in bugs_by_type:
        recommendations.append(
            "Reduce hallucinations by constraining AI responses to only information "
            "explicitly mentioned in conversation"
        )
    
    if 'verbose' in bugs_by_type:
        recommendations.append(
            "Keep responses shorter (under 40 words) for more natural conversation flow"
        )
    
    if 'unhelpful' in bugs_by_type:
        recommendations.append(
            "Avoid unhelpful responses like 'I don't know' - always provide useful alternatives"
        )
    
    if not recommendations:
        recommendations.append(
            "System performing well - continue monitoring for edge cases"
        )
    
    return recommendations