# GPT Nexus: Open-Source Agent Platform

## Introduction

GPT Nexus is an innovative, open-source platform developed to assist in the development, testing, and hosting of GPT Agents. It is being developed in tandem with writing the book GPT Agents In Action from Manning Publications. The platform is built upon the Python web application framework Streamlit, and offers a user-friendly chat and dashboard interface. This platform facilitates the creation of intelligent dashboards, prototypes, and GPT chat applications, making it a versatile tool for developers at all levels.

Designed with simplicity, exploration, and power in mind, GPT Nexus stands out in a crowded field of over one hundred GPT platforms and toolkits. Unlike other tools, which range from basic toolkits like Semantic Kernel or LangChain to complete platforms like AutoGen and CrewAI, GPT Nexus focuses on teaching the core concepts of building full-featured GPT agents. It integrates seamlessly with profiles/personas and actions/tools, allowing users to extend its capabilities according to their needs.

## Features
GPT Nexus will support the following features:
- **Profiles/Personas**: Define the primary persona and profile for the agent, including the personality and primary motivator, enabling the agent to respond to requests accurately.
- **Actions/Tools**: Utilize semantic/prompt or native/code functions as actions that an agent can take, enhancing the flexibility and capability of the agent.
- **Knowledge/Memory**: Incorporate additional information and various aspects of memory, from short-term to semantic memory, improving the agent's responsiveness and accuracy.
- **Planning/Feedback**: Select options for the type of planning and feedback an agent uses, allowing for more sophisticated decision-making processes.
- **Multi-Agents Support**: Manage multiple agents, facilitating complex interactions and scenarios.

## Getting Started

### Installation

To begin using GPT Nexus, you need to set up a Python virtual environment (version 3.10 recommended). If you're unfamiliar with creating a virtual environment, please refer to Appendix B of the book this platform accompanies.

#### Quick Setup

```bash
# Install GPT Nexus directly from the GitHub repository
pip install git+https://github.com/cxbxmxcx/GPT-Nexus.git

# Set your OpenAI API Key
export OPENAI_API_KEY="<your API key>"
# or for Windows PowerShell
$env:OPENAI_API_KEY="<your API key>"
# or create a .env file with your API key
echo 'OPENAI_API_KEY="<your API key>"' > .env

# Run the application
nexus run
```

After running the application, a web interface will launch, allowing you to log in or create a new user and start interacting with an agent.

#### Development Setup

For those interested in contributing to GPT Nexus or customizing it further:

```bash
# Clone the GPT Nexus repository 
git clone https://github.com/cxbxmxcx/GPT-Nexus.git

# Install the cloned repository in editable mode
pip install -e GPT-Nexus

# Follow the same steps as above to set your OpenAI API Key and run the application
```

## Building a Chat Application with Streamlit

GPT Nexus utilizes Streamlit for its web interface, offering a straightforward and powerful tool for creating Python web applications. The book GPT Agents In Action provides detailed instructions on building a chat interface against the OpenAI API, utilizing direct and streaming responses to enhance user engagement.

## Conclusion

GPT Nexus represents a significant step forward in the development of GPT agents, providing a comprehensive, easy-to-use platform for developers of all levels. By following the steps outlined in this README, you can start exploring the capabilities of GPT Nexus and contribute to the evolving landscape of GPT applications.



