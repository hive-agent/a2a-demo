import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import EvenOrOddAgentExecutor

def main():
    skill = AgentSkill(
        id="even_or_odd",
        name="even_or_odd",
        description="Determine if a number is even or odd",
        tags=["math"],        
    )
    
    agent_card = AgentCard(        
        name="Even or Odd Agent",
        description="Determine if a number is even or odd",
        url="http://localhost:8000/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        version="1.0.0",
        capabilities=AgentCapabilities(),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=EvenOrOddAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )
    
    app = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    uvicorn.run(app.build(), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
