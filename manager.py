#manager
import anthropic
import json
import time
import uuid
import redis
from queue import Queue

ANTHROPIC_API_KEY = 'API_KEY'
REDIS_HOST = 'localhost' 
REDIS_PORT = 6379
REDIS_DB = 0 

client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
redis_conn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB) 

TASK_QUEUE = 'task_queue'
REVIEW_QUEUE = 'review_queue'

def get_claude_response(prompt, model="claude-v1"):
    response = client.completion(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        model=model,
        max_tokens_to_sample=2048,
    )
    return response.completions[0].text

def break_down_requirements(user_requirements):
    # TODO: Improve this prompt to break down into multiple tasks
    prompt = (
        f"User Requirements: {user_requirements}\n\n"
        f"Instructions:\n"
        f"1. Analyze the requirements and break them into smaller coding tasks.\n"
        f"2. Structure the output as a JSON array, with each element representing a task.\n"
        f"3. Each task object should include: 'task_id', 'description', 'language', 'status', 'assigned_to', 'code', 'review_feedback'.\n"
        f"4. Set 'language' based on keywords (e.g., 'Python' for 'Python app', 'JavaScript' for 'web app').\n"
        f"5. Set initial 'status' to 'pending', 'assigned_to' to None, 'code' to None, and 'review_feedback' to None.\n\n"
        f"Example Output (JSON):\n"
        f"[{'task_id': '...', 'description': '...', 'language': '...', 'status': '...', 'assigned_to': None, 'code': None, 'review_feedback': None}, ...]" 
    )

    response = get_claude_response(prompt)
    try:
        tasks = json.loads(response) 
        return tasks
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from Claude's response.\nResponse: {response}")
        return [] 

def review_code(task):
    # TODO: Improve the code review prompt
    prompt = (
        f"Task Description: {task['description']}\n"
        f"Code: {task['code']}\n\n"
        f"Instructions:\n"
        f"1. Review the code for correctness, efficiency, and adherence to best practices in {task['language']}.\n"
        f"2. Provide constructive feedback and specific suggestions for improvement (if any).\n"
        f"3. If the code is satisfactory, indicate approval."
    )
    feedback = get_claude_response(prompt)
    return feedback

def main():
    while True:
        user_requirements = input("Enter project requirements (or 'exit'): ")
        if user_requirements.strip().lower() == 'exit':
            break 

        tasks = break_down_requirements(user_requirements) 
        if tasks: 
            for task in tasks:
                task['task_id'] = str(uuid.uuid4()) # Ensure unique ID
                redis_conn.rpush(TASK_QUEUE, json.dumps(task))

            print(f"Added {len(tasks)} tasks to the queue.")

            completed_tasks = []
            while len(completed_tasks) < len(tasks):
                # Check for completed tasks in the review queue
                review_task = redis_conn.lpop(REVIEW_QUEUE)
                if review_task:
                    task = json.loads(review_task)

                    # TODO: 
                    # - Potentially get reviews from multiple developers 
                    #   before sending to the manager for final review. 

                    feedback = review_code(task)
                    print(f"Review Feedback for {task['task_id']}: {feedback}")

                    # TODO: Implement more robust consensus mechanism 
                    if "approval" in feedback.lower(): 
                        task['status'] = 'complete'
                        completed_tasks.append(task)
                    else:
                        # Send back for rework (to the same developer for now)
                        task['status'] = 'pending'
                        task['review_feedback'] = feedback
                        redis_conn.rpush(TASK_QUEUE, json.dumps(task))

                    print(f"Task {task['task_id']} status: {task['status']}")

                time.sleep(2)  

            print("\n--- Final Results ---")
            for task in completed_tasks:
                print(f"Task: {task['description']}\nCode:\n{task['code']}\n")

if __name__ == "__main__":
    main()