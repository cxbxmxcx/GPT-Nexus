import pytest

from gpt_nexus.nexus_base.chat_models import PromptTemplate
from gpt_nexus.nexus_base.chat_system import ChatSystem
from gpt_nexus.nexus_base.prompt_template_manager import PromptTemplateManager


@pytest.fixture
def nexus():
    # Create an instance of ChatSystem for testing
    return ChatSystem()


@pytest.fixture
def prompt_template_manager(nexus):
    # Create an instance of PromptTemplateManager for testing
    return PromptTemplateManager(nexus)


@pytest.fixture
def agent(nexus):
    # Create an instance of Agent for testing
    agent_name = "GroqAgent"
    profile_name = "Adam"
    agent = nexus.get_agent(agent_name)
    profile = nexus.get_profile(profile_name)
    agent.profile = profile
    return nexus.get_agent(agent_name)


def test_execute_simple_input_template(prompt_template_manager, agent):
    # Define the test inputs
    content = """
        type: prompt
        inputs:
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, oprompt, result = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John, what is your name?\n"
    assert oprompt is None
    assert result is not None


def test_get_prompt_template_with_monkeypatch(nexus, monkeypatch):
    # Function to replace get_prompt_template
    def mock_get_prompt_template():
        return "Your mock template"

    # Use monkeypatch to replace the real function with your mock
    monkeypatch.setattr(nexus, "get_prompt_template", mock_get_prompt_template)

    # Now calling nexus.get_prompt_template() will use the mock function
    result = nexus.get_prompt_template()
    assert result == "Your mock template"


def test_execute_partial_input_template(prompt_template_manager, agent, monkeypatch):
    # Define the test inputs
    def mock_get_prompt_template(self):
        content = """        
        inputs:
            type: function
            name:
                type: string
            template: |
                {{name}} - {{name}}
        """
        return PromptTemplate(
            content=content, inputs={}, outputs={}, name="partial_test"
        )

    # Use monkeypatch to replace the real function with your mock
    monkeypatch.setattr(
        prompt_template_manager, "get_prompt_template", mock_get_prompt_template
    )
    content = """        
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{>partial_test name}}, what is your name?"""
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, oprompt, result = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John- John\n, what is your name?"
    assert oprompt is None
    assert result is not None


def test_execute_template(prompt_template_manager, agent):
    # Define the test inputs
    content = """
        type: prompt
        inputs:
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
        outputs:
            output:
                type: string                
            template: "Hello, {{ output }}!"
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, oprompt, result = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "What is your name?"
    assert oprompt == "Hello, John!"
    assert result == "Hello, John!"

    # Add more test cases as needed
