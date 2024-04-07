import re
from typing import List

from pybars import Compiler

from gpt_nexus.nexus_base.chat_models import PromptTemplate, db


class PromptTemplateManager:
    def __init__(self, nexus):
        self.nexus = nexus

    def add_prompt_template(
        self, template_name, template_content, template_inputs, template_outputs
    ):
        if isinstance(template_inputs, List):
            template_inputs = ",".join(template_inputs)
        if isinstance(template_outputs, List):
            template_outputs = ",".join(template_outputs)
        with db.atomic():
            if (
                PromptTemplate.select()
                .where(PromptTemplate.name == template_name)
                .exists()
            ):
                raise ValueError("Template name already exists")
            PromptTemplate.create(
                name=template_name,
                content=template_content,
                inputs=template_inputs,
                outputs=template_outputs,
            )
            print(f"Prompt template '{template_name}' added.")
            return True

    def get_prompt_template(self, template_name):
        try:
            return PromptTemplate.get(PromptTemplate.name == template_name)
        except PromptTemplate.DoesNotExist:
            return None

    def update_prompt_template(
        self, template_name, template_content, template_inputs, template_outputs
    ):
        if isinstance(template_inputs, List):
            template_inputs = ",".join(template_inputs)
        if isinstance(template_outputs, List):
            template_outputs = ",".join(template_outputs)
        with db.atomic():
            template = PromptTemplate.get(PromptTemplate.name == template_name)
            template.content = template_content
            template.inputs = template_inputs
            template.outputs = template_outputs
            template.save()
            print(f"Prompt template '{template_name}' updated.")
            return True

    def delete_prompt_template(self, template_name):
        with db.atomic():
            query = PromptTemplate.delete().where(PromptTemplate.name == template_name)
            return query.execute()

    def get_prompt_template_names(self):
        return [template.name for template in PromptTemplate.select()]

    def split_prompt_function_text(self, text, separator="# -- #"):
        # Splitting the text at the specified separator
        parts = text.split(separator)

        # If the separator is not found, parts will contain the entire text in the first element.
        # Therefore, it's good to check the length of parts to handle different cases.
        if len(parts) > 1:
            return parts[0], parts[1]
        else:
            # Handling the case where the separator is not found
            # You can adjust this to return something else if needed
            return text, ""

    def execute_template(
        self, agent, content, inputs, outputs, partial_execution=False
    ):
        nexus = self.nexus
        input_prompt, code = self.split_prompt_function_text(content)

        # Dynamically execute the helper functions code string
        exec(code, locals())
        # Initialize an empty helpers dictionary
        helpers = {}
        # Assuming your code string only contains helper functions,
        # and each function name starts with an underscore (_),
        # dynamically add them to the helpers dictionary.
        # This part relies on the convention that helper function names are prefixed with '_'.
        response_handler = None
        for name, obj in locals().items():
            if callable(obj):
                if name == "__response__":
                    response_handler = obj
                elif name.startswith("_"):
                    # Remove the leading underscore from the helper's name when adding it to the helpers dictionary
                    helper_name = name[1:]
                    helpers[helper_name] = obj

        def parse_partials(text):
            # Pattern to match strings that start with '{{>' and end with '}}'
            pattern = r"\{\{>(.*?)\}\}"

            # Find all matches
            matches = re.findall(pattern, text)

            # Parse each match to separate the name from the options
            partials = []
            for match in matches:
                parts = match.strip().split(" ", 1)  # Split on the first space only
                partial = {
                    "name": parts[0],
                    "options": parts[1] if len(parts) > 1 else None,
                }
                partials.append(partial)
            return partials

        prompt = input_prompt
        for partial in parse_partials(input_prompt):
            partial_name = partial["name"]
            partial_options = partial["options"]
            partial_template = self.get_prompt_template(partial_name)
            if partial_template:
                partial_content = partial_template.content
                partial_inputs = (
                    partial_template.inputs.split(",")
                    if partial_template.inputs
                    else []
                )
                tinputs = {}
                for input_name in partial_inputs:
                    tinputs[input_name] = inputs.get(input_name)
                partial_outputs = (
                    partial_template.outputs.split(",")
                    if partial_template.outputs
                    else []
                )
                partial_result = self.execute_template(
                    agent,
                    partial_content,
                    tinputs,
                    partial_outputs,
                    partial_execution=True,
                )
                # Replace the partial placeholder with the partial result
                prompt = prompt.replace(
                    f"{{{{>{partial_name} {partial_options}}}}}", partial_result
                )

        compiler = Compiler()
        template = compiler.compile(prompt)
        prompt = template(inputs, helpers=helpers)

        if partial_execution:
            return prompt

        result = agent.get_semantic_response(agent.profile.persona, prompt)

        if response_handler:
            result = response_handler(result)

        return prompt, result

        # # Retrieve the expected outputs from metadata for wrapping the output
        # output_keys = [
        #     output.split(":")[0] for output in metadata["outputs"].split(",") if output
        # ]

        # # Dynamically create a function from the loaded code
        # exec(code, globals())
        # func = globals().get(name)
        # if func and isinstance(func, types.FunctionType):
        #     # Inject the Nexus instance into the function's globals
        #     func_globals = func.__globals__
        #     func_globals["nexus"] = self.nexus

        #     # Prepare arguments by inspecting the function signature
        #     sig = inspect.signature(func)
        #     sig_params = sig.parameters.keys()

        #     # Check if all expected inputs are provided
        #     missing_inputs = [param for param in sig_params if param not in kwargs]
        #     if missing_inputs:
        #         return {
        #             "error": f"Missing required inputs: {', '.join(missing_inputs)}"
        #         }

        #     func_args = {k: kwargs[k] for k in sig_params if k in kwargs}

        #     # Execute the function
        #     result = func(**func_args)

        #     # Wrap the output based on defined outputs
        #     if not output_keys:
        #         # If no outputs are defined, return the raw result
        #         output = {"result": result}
        #     elif len(output_keys) == 1:
        #         # For a single defined output
        #         output = {output_keys[0]: result}
        #     else:
        #         # For multiple outputs defined, assumes the function returns a tuple
        #         output = dict(zip(output_keys, result))

        #     return output
        # else:
        #     return {"error": "Function not found or is not callable."}
