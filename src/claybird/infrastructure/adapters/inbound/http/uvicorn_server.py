import uvicorn
from claybird.application.ports.inbound.server_port import ServerPort

class UvicorServer(ServerPort):

    async def run(self, app, host, port):
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()