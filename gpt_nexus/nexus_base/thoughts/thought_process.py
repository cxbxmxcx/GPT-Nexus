import os
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel

from gpt_nexus.nexus_base.thoughts.thought_executor import ThoughtExecutor


class ThoughtNode(BaseModel):
    id: str
    type: str
    target: Optional[str] = None
    persona: Optional[str] = None
    action: Optional[str] = None
    output: Optional[Any] = None

    def execute(self, context: Dict[str, Any], process: "ThoughtProcess"):
        executor = ThoughtExecutor()
        executor.execute_action(self.action, context)
        # # Check for and process any partials before execution
        # self.process_partials(self.action, context, process)
        # if self.type == "prompt":
        #     self.output = self.simulate_prompt(context)
        # elif self.type == "function":
        #     self.output = self.simulate_function(context)
        # elif self.type == "condition":
        #     self.output = self.simulate_condition(context)

    # def simulate_prompt(self, context: Dict[str, Any]) -> str:
    #     return "Simulated output for prompt"

    # def simulate_function(self, context: Dict[str, Any]) -> str:
    #     return "Simulated function result"

    # def simulate_condition(self, context: Dict[str, Any]) -> bool:
    #     return eval(context.get(self.id, ""))

    # def process_partials(
    #     self, action: str, context: Dict[str, Any], process: "ThoughtProcess"
    # ):
    #     if action:
    #         import re

    #         partials = re.findall(r"{{>([^}]+)}}", action)
    #         for partial in partials:
    #             if partial.endswith(".yaml"):
    #                 new_nodes, new_sequence = load_yaml_partial(partial)
    #                 process.nodes.update(new_nodes)
    #                 process.sequence.extend(new_sequence)


def load_yaml_partial(filepath: str) -> Tuple[Dict[str, ThoughtNode], List[str]]:
    with open(filepath, "r") as file:
        data = yaml.safe_load(file)
    nodes = {node["id"]: ThoughtNode(**node) for node in data["thoughts"]}
    sequence = data["sequence"]
    return nodes, sequence


class ThoughtProcess(BaseModel):
    nodes: Dict[str, ThoughtNode]
    sequence: Optional[List[str]] = []

    def __init__(self, template, nexus=Depends(get_nexus)):
        template = self.load_template_data(template)
        nodes, sequence = self.parse_template(template)
        super().__init__(nodes=nodes, sequence=sequence)

    def think(self, initial_input: str) -> Dict[str, Any]:
        context = {"input": initial_input}
        current_index = 0
        if self.sequence:
            while current_index < len(self.sequence):
                node_id = self.sequence[current_index]
                node = self.nodes[node_id]
                node.execute(context, self)
                context[node.id] = node.output

                if node.type == "condition":
                    if not node.output:
                        target_node_id = node.target
                        if target_node_id in self.nodes:
                            current_index = self.sequence.index(target_node_id)
                            continue
                    else:
                        break
                current_index += 1
        else:
            for node_id, node in self.nodes.items():
                node.execute(context, self)
                context[node.id] = node.output

        return context

    def load_template_data(self, content):
        template_data = None
        try:
            template_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            if hasattr(e, "problem_mark"):
                mark = e.problem_mark
                error_message = (
                    f"Error at line {mark.line + 1}, column {mark.column + 1}: {str(e)}"
                )
            else:
                error_message = str(e)
            raise ValueError(
                f"Error loading YAML content: {error_message}\n\n{content}"
            )
        return template_data

    def parse_template(self, data: Dict) -> "ThoughtProcess":
        nodes = {node["id"]: ThoughtNode(**node) for node in data["thoughts"]}
        return nodes, data.get("sequence", [])


# Example Usage
current_dir = os.path.dirname(os.path.abspath(__file__))
thought_path = os.path.join(current_dir, "thought_single.yaml")
with open(thought_path, "r") as file:
    thoughts = file.read()
thought_process = ThoughtProcess(thoughts)
result = thought_process.think("Initial problem input")
print(result)
