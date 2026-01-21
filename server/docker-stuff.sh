docker build -t invoke-copilot-studio-mcp-server .

docker stop invoke-copilot-studio-mcp-server
docker rm invoke-copilot-studio-mcp-server

docker run -d -p 8000:8000 --env-file .env --name invoke-copilot-studio-mcp-server invoke-copilot-studio-mcp-server
docker logs -f invoke-copilot-studio-mcp-server