import uuid

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TextPart,
)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"
BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        resolver = A2ACardResolver(
            httpx_client=client,
            base_url=BASE_URL,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            print(f"Resolving agent card from {BASE_URL}{PUBLIC_AGENT_CARD_PATH}")

            _public_card = await resolver.get_agent_card()
            ##print(f"Resolved agent card: {_public_card.model_dump_json(indent=2)}")

            final_agent_card_to_use = _public_card
        
        except Exception as e:
            print(f"Error resolving agent card: {e}")
            raise RuntimeError(f"Error resolving agent card: {e}")
        
        client = A2AClient(
            httpx_client=client,
            agent_card=final_agent_card_to_use,            
        )

        print("Agent2Agent client initialized")

        message_payload = Message(
            role=Role.user,
            messageId=str(uuid.uuid4()),
            parts=[Part(root=TextPart(text="134560"))],
        )

        request = SendMessageRequest(
            id=str(uuid.uuid4()),
            params=MessageSendParams(
                message=message_payload,
            ),
        )

        print("Sending message to agent")

        response = await client.send_message(request)
        print(f"Response: {response.model_dump_json(indent=2)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
