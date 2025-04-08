from client.ollama.client import OllamaMCPClient


class ClientFactory:
    def __init__(self):
        pass

    def create_client(self, client_type: str):
        """
        Create a client based on the specified type.
        
        Args:
            client_type: The type of client to create ('ollama' or 'openai')
        """
        
        if(client_type == "ollama"):
            return OllamaMCPClient()
        elif(client_type == "openai"):
            raise NotImplementedError("OpenAI client not implemented")
        else:
            return OllamaMCPClient()
        
        pass
