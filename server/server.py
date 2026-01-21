import logging
import msal
import os

from fastmcp import FastMCP, Context
from fastmcp.server.auth.providers.azure import AzureProvider
from fastmcp.server.dependencies import get_http_headers, get_access_token
from mcp.types import TextContent, ImageContent
from microsoft_agents.activity import ActivityTypes, load_configuration_from_env
from microsoft_agents.copilotstudio.client import (
    ConnectionSettings,
    CopilotClient,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

auth_provider = AzureProvider(
    client_id=os.environ.get("COPILOTSTUDIOAGENT__AGENTAPPID"),  # Your Azure App Client ID
    client_secret=os.environ.get("COPILOTSTUDIOAGENT__CLIENTSECRET"),                 # Your Azure App Client Secret
    tenant_id=os.environ.get("COPILOTSTUDIOAGENT__TENANTID"), # Your Azure Tenant ID (REQUIRED)
    base_url="http://localhost:8000",                   # Must match your App registration
    required_scopes=["invoke"],                 # At least one scope REQUIRED - name of scope from your App
)


mcp = FastMCP("FastMCP Invoke Copilot Studio Server", auth=auth_provider)


def acquire_token(settings, app_client_id, tenant_id):
    # --- IGNORE ---
    pass
    # --- IGNORE ---


def create_client():
    settings = ConnectionSettings(
        environment_id=os.environ.get("COPILOTSTUDIOAGENT__ENVIRONMENTID"),
        agent_identifier=os.environ.get("COPILOTSTUDIOAGENT__SCHEMANAME"),
        cloud=None,
        copilot_agent_type=None,
        custom_power_platform_cloud=None,
    )
    logger.info(f"Configuring settings...")
    mcptoken = get_access_token()
    logger.info(f"Got MCP ...")
    confidentialcredential = msal.ConfidentialClientApplication(
        os.environ.get("COPILOTSTUDIOAGENT__AGENTAPPID"),
        authority=f"https://login.microsoftonline.com/{os.environ.get('COPILOTSTUDIOAGENT__TENANTID')}",
        client_credential=os.environ.get("COPILOTSTUDIOAGENT__CLIENTSECRET")
    )
    logger.info(f"Acquiring Copilot Studio token on behalf of MCP token...")
    copilottoken = confidentialcredential.acquire_token_on_behalf_of(
        user_assertion=mcptoken.token,
        scopes=["https://api.powerplatform.com/.default"]
    )
    logger.info(f"Acquired Copilot Studio token: {copilottoken}")

    copilot_client = CopilotClient(settings, copilottoken["access_token"])
    return copilot_client

@mcp.tool
async def get_user_info() -> dict:
    """Returns information about the authenticated Azure user."""
    
    token = get_access_token()
    # The AzureProvider stores user data in token claims
    return {
        "azure_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
        "job_title": token.claims.get("job_title"),
        "office_location": token.claims.get("office_location")
    }


@mcp.tool
async def invoke(query: str, ctx: Context) -> str:
    headers = get_http_headers()
    
    logger.info(f"invoke called: {{'query': '{query}', 'headers': {headers}}}")
    copilot_client = create_client()
    act = copilot_client.start_conversation(True)
    logger.info("Starting conversation...")
    async for action in act:
        if action.text:
            logger.info(action.text)
            conversation_id = action.conversation.id
    logger.info(f"Conversation ID: {conversation_id}")
    replies = copilot_client.ask_question(query, conversation_id)
    async for reply in replies:
        if reply.type == ActivityTypes.message:
            return reply.text    


if __name__ == "__main__":
    logger.info("Starting FastMCP Invoke Copilot Studio Server", extra={"host": "0.0.0.0", "port": 8000})
    mcp.run(transport="http", host="0.0.0.0", port=8000)