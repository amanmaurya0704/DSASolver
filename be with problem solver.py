from autogen_agentchat.agents import CodeExecutorAgent
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import asyncio
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.tools import FunctionTool
from autogen_agentchat.ui import Console
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")


# Initialize the OpenAI model client
openai_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=api_key)

docker = DockerCommandLineCodeExecutor(
    work_dir='tmp',
    timeout=120
)
termination_condition = TextMentionTermination("STOP")

problem_solver = AssistantAgent(
    name='problem_solver',
    model_client=openai_client,
    description="An expert agent that solves problems using code execution. ",
    system_message="You are a problem solver agent that is an expert in solving DSA problems,"\
    "You will be working with code executor agent to execute code."\
    "You will be given task and you should first provide a way to solve the task/problem"\
    "Then you should give the code in Python block format so that it can be ran by code executor agent"\
    "you should only give single code block and pass it to code executor agent"\
    "In case of any error you should give the correct code in Python Block format"\
    "once the code run successfully executed and you have the results. You should explain the result in details."\
    "Make sure each code has 3 test cases and output of each test case and timeout of each test case is printed"\
    "Once everything is done, you should explain the result and say 'STOP' to stop the conversation"
)



code_executor = CodeExecutorAgent(
    name='code_executor',
    code_executor=docker
)

task = TextMessage(
    content ='''Here is some code
```python
print('Hello World ')
```
''',
source="user"
)

team = RoundRobinGroupChat(
    participants=[problem_solver, code_executor],
    termination_condition=termination_condition,
    max_turns=10
)


async def run_code_executor_agent():
    try:
        await docker.start()
        task = "Write a code to check if number is prime or not."
        async for message in team.run_stream(task = task):
            print("-"*50)
            if isinstance(message, TextMessage):
                print("Message from : ",message.source)
                print("Content : ",message.content)
            else:
                print(message)
            print("-"*50)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        await docker.stop()

if __name__ == '__main__':
    import asyncio
    asyncio.run(run_code_executor_agent())
    print("Code Execution Completed")