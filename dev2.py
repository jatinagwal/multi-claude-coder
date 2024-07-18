import anthropic
import json
import time
import redis


ANTHROPIC_API_KEY = 'API_KEY'
REDIS_HOST = 'localhost' 
REDIS_PORT = 6379
REDIS_DB = 0

client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
redis_conn = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

TASK_QUEUE = 'task_queue'
REVIEW_QUEUE = 'review_queue' 

DEV_ID = "dev2"

def get_claude_response(prompt, model="claude-v1"):
    response = client.completion(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        model=model,
        max_tokens_to_sample=2048,
    )
    return response.completions[0].text

def generate_code_for_task(task):
    # TODO: Improve this prompt template 
    prompt = (
        f"Task Description: {task['description']}\n"
        f"Programming Language: {task['language']}\n"
        f"Generate {task['language']} code for this task:\n"
    ) 
    code = get_claude_response(prompt)
    return code

if __name__ == "__main__":
    task_queue = Queue() 
    
    while True:
        try: 
            task = task_queue.get(block=True, timeout=1)  # Wait for a task

            # TODO:
            # - Mark task as 'in_progress'
            # - Generate code using the improved `generate_code_for_task`
            # - Update task with generated code
            # - Place the completed task in a 'review_queue' (to be created)
            # - Handle potential errors 

            print(f"{DEV_ID} processed task: {task['task_id']}")

        except Exception as e:  
            # TODO: Implement more specific error handling
            print(f"{DEV_ID} - Error: {e}") 
            time.sleep(1)