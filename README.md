# Smart Compiler Infrastructure

This project introduces an agentic approach for high-level 
and multi-purpose compilers.CI4AI.

# TUTORIALS

This Smart Compiler uses AI models and traditional compiler techniques to enhance the performance scalability of C programs and Python programs. By profiling, and finding approaches for optimizations.

# Sofwate Requirements

## Install the project
For dependency management and installation, this project uses ```uv```.
See [Astral Documentation](https://docs.astral.sh/uv) for installing the uv package manager.


## Project dependencies

### Packages
After installing **uv** run: ```uv sync``` for syncing project dependencies.

### Ollama
To deploy a LLM using ollama first we need to install Ollama by following 
its [Official Documentation](https://ollama.com).

Once Ollama is installed deploy the Ollama server (if it was not deployed by the installation).



### Quick Ollama deploy
1. Serve the Ollama server: ```ollama serve``` (if it is not already deployed).
2. Create LLM model using the SmartCompiler Modelfile: ```ollama create llama3.1-smart-compiler -f ollama-smart-compiler-Modelfile```.
3. Run the created LLM: ```ollama run llama3.1-smart-compiler:latest```.
4. If it opens a chat after running the LLM, just type ```/bye``` to close that chat.

#### Setting up Environment variables
Set up the environment variables in a ```.env``` file.
An example of how this file looks like.
```
# .env
OLLAMA_MODEL=llama3.1-smart-compiler:latest
OLLAMA_HOST=http://localhost:11434
MCP_SERVER_SCRIPT_PATH=<project_folder>/src/server_main.py
MCP_SERVER_TRANSPORT=stdio
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_TRANSPORT=stdio
MCP_SERVER_OLLAMA_MODEL=llama3.1:latest
LOG_LEVEL=INFO # OR DEBUG
```

Then type : export $(cat .env | xargs)


# How-To Guides

## Running the project
For running the project, once all dependencies and configurations are set, run the following command:

```bash
python src/main.py

```

Then the smart compiler will ask the user to provide the folder of the project that the user will be working on. Please provide a path example : /home/directory/projectAI

Then the smart compiler will ask which specific file will the smart compiler work on: type the name fo the file, exmaple : api_server.py

Then the smart compiler will ask which specific task to do: Profile or Optimize. Type what you would like to do with the program.

### USE CASE
```bash
python src/main.py

Please provide the folder of your project: /home/user/Desktop/SmartCompiler/examples/jacobi-2d
Please provide the file you want to analyze: main.c
File 'main.c' found in the project.

What do you want to do with the file? (Profile or Optimize): Profile
```
The profile information or the optimize C application will be stored in the same folder where the target project is located.


### Explanation

Details about the smart compiler can be found on the following diagramas:
- **Diagrams**:  
  - [Diagram 1](https://drive.google.com/file/d/1S5gRxw_vizR1XnmbiZnAH1yZnkB8Ep0_/view?usp=drive_link)  
  - [Diagram 2](https://drive.google.com/file/d/1tgCcINlzBUe6A1PCNX6R_ftAnb9WidcA/view?usp=sharing)

## References

To deploy a LLM using ollama first we need to install Ollama by following 
its [Official Documentation](https://ollama.com)

## Acknowledgements

National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)


## Internal Notes

### To extract Modelfile

```ollama show --modelfile llama3.1 > Modelfile```

### To create from Modelfile

```ollama create llama3.1-tool -f Modelfile```





