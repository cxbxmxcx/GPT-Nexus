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
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John, what is your name?\n"
    assert oprompt is None
    assert iresult is not None
    assert oresult is None


def test_bad_yaml_input_template(prompt_template_manager, agent):
    # Define the test inputs
    content = """
    inputs: -
        type: prompt
        inputs:
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("Error loading YAML content:")

    assert exception


def test_bad_yaml_output_template(prompt_template_manager, agent):
    # Define the test inputs
    content = """
    outputs: -
        type: string
        template: |
            Hello, {{ output }}!
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("Error loading YAML content:")

    assert exception


def test_bad_template_content(prompt_template_manager, agent):
    # Define the test inputs
    content = """
    inputs:
        type: prompt
        name:
            type: string
        template: |
            I am {{ name }, what is your name?    
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    exception = True
    try:
        iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
            agent, content, inputs, outputs={}, partial_execution=False
        )
        exception = False
    except Exception as e:
        assert str(e).startswith("No terminal matches")

    assert exception


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
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt == "I am John - John\n, what is your name?"
    assert oprompt is None
    assert iresult is not None
    assert oresult is None


def test_execute_template(prompt_template_manager, agent):
    # Define the test inputs
    content = """        
        inputs:
            type: prompt
            name:
                type: string
            template: |
                I am {{ name }}, what is your name?
        outputs:
            type: function
            output:
                type: string                
            template: "Hello, {{ output }}!"
    """
    inputs = {"name": "John"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "I am John, what is your name?\n"
    assert iresult is not None
    assert oprompt.startswith("Hello,")
    assert oresult is not None


def test_helper_template(prompt_template_manager, agent):
    content = """        
        inputs:
            input:
                type: string
            template: |
                {{#upper input}}
        helpers:
            upper: |
                def upper(arg):
                    return arg.upper()          
    """
    inputs = {"input": "hello"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "HELLO\n"
    assert iresult == "HELLO\n"


def test_template_multiple_args(prompt_template_manager, agent):
    content = """        
        inputs:
            type: function
            input:
                type: string
            name:
                type: string
            template: |
                {{input}}   {{name}}
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt.startswith("hello   world")
    assert iresult.startswith("hello   world")


def test_helper_template_multiple_args(prompt_template_manager, agent):
    content = """        
        inputs:
            input:
                type: string
            name:
                type: string
            template: |
                {{#add input name}}
        helpers:
            add: |
                def add(arg1, arg2):
                    return arg1.upper() + arg2         
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "HELLOworld\n"
    assert iresult == "HELLOworld\n"

    # Add more test cases as needed


def test_input_output_prompts(prompt_template_manager, agent):
    content = """        
        inputs:
            type: prompt
            input:
                type: string
            name:
                type: string
            template: |
                {{input}}   {{name}}
        outputs:
            type: prompt
            output:
                type: string
            name:
                type: string
            template: |
                {{output}}   {{name}}
    """
    inputs = {"input": "hello", "name": "world"}
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == "hello   world\n"
    assert iresult is not None
    assert oprompt.endswith("world\n")
    assert oresult is not None


def test_reasoning_evaluation_partials(prompt_template_manager, agent, monkeypatch):
    # Define the test inputs
    def mock_get_prompt_template(arg):
        if arg == "reasoning":
            content = """        
            inputs:
                type: prompt
                input:
                    type: string
                template: |
                    Generate a chain of thought reasoning strategy 
                    in order to solve the following problem. 
                    Just output the reasoning steps and avoid coming
                    to any conclusions. Also, be sure to avoid any assumptions
                    and factor in potential unknowns.
                    {{input}}
            """
        elif arg == "evaluation":
            content = """        
            inputs:
                type: prompt
                input:
                    type: string
                output:
                    type: string
                template: |
                    Provided the following problem:
                    {{input}}
                    and the solution {{output}}
                    Evaluate how successful the problem 
                    was solved and return a score 0.0 to 1.0.
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
            input:
                type: string
            template: |
                problem: {{input}}
                reasoning: {{>reasoning input}}

        outputs:
            type: prompt
            input:
                string
            output:
                type: string
            template: |
                evaluation: {{>evaluation input output}}
    """
    inputs = {"input": "who would win a peck off, a rooster or a tiger?"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    # Perform assertions to verify the expected outputs
    assert iprompt.startswith(
        "problem: who would win a peck off, a rooster or a tiger?"
    )
    assert oprompt is not None
    assert iresult is not None
    assert oresult is not None


def test_helper_agent_functions(prompt_template_manager, agent):
    content = """        
        inputs:
            type: function            
            template: |                
                Agent type: {{#agent_name}} Memory: {{#memory_store}}
        helpers:
            agent_name: |
                def agent_name():
                    return agent.name
            memory_store: |
                def memory_store():
                    return agent.memory_store        
    """
    inputs = {}
    agent.memory_store = "my_memory"
    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt == f"Agent type: {agent.name} Memory: {agent.memory_store}\n"
    assert iresult == f"Agent type: {agent.name} Memory: {agent.memory_store}\n"
    assert oprompt is None
    assert oresult is None


def test_helper_nexus_functions(prompt_template_manager, agent):
    content = """        
        inputs:
            type: function 
            agent:
                type: string         
            template: |                
                Agent: {{#get_agent agent}} 
                Users: {{#get_users}}
        helpers:
            get_agent: |
                def get_agent(agent_name):
                    return nexus.get_agent(agent_name).name
            get_users: |
                def get_users():
                    users = nexus.get_all_participants()
                    return str(users)
    """
    inputs = {"agent": "GroqAgent"}

    # Call the execute_template function
    iprompt, iresult, oprompt, oresult = prompt_template_manager.execute_template(
        agent, content, inputs, outputs={}, partial_execution=False
    )

    assert iprompt is not None
    assert iresult is not None
    assert oprompt is None
    assert oresult is None

    # Add more test cases as needed

    # inputs:
    #     type: prompt
    #     input:
    #         type: string
    #     template: |
    #         {{>header input}}

    #         {{#augment_memory input}}

    #         {{#augment_knowledge input}}

    #     outputs:
    #     type: function
    #     output:
    #         type: string
    #     template: "{{#format output}}"

    #     helpers:
    #     # Defines a method to augment the memory of the input
    #     augment_memory: |
    #         def augment_memory(this, arg):
    #             aug = arg
    #             if agent.memory_store:
    #                 aug = nexus.apply_memory_RAG(agent.memory_store, arg, agent)
    #             return aug

    #     # Defines a method to augment the knowledge of the input
    #     augment_knowledge: |
    #         def augment_knowledge(this, arg):
    #             aug = arg
    #             if agent.knowledge_store:
    #                 aug = nexus.apply_knowledge_RAG(agent.knowledge_store, arg)
    #             return aug

    #     # Modifies the response to uppercase
    #     format: |
    #         def format(response):
    #             return response.upper()
