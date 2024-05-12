from gpt_nexus.nexus_base.chat_models import ThoughtTemplate, db
from gpt_nexus.nexus_base.thought_engine import ThoughtEngine


class ThoughtTemplateManager:
    def __init__(self, nexus):
        self.nexus = nexus
        self.thought_engine = ThoughtEngine(nexus)

    def add_thought_template(self, template_name, template_content):
        with db.atomic():
            if (
                ThoughtTemplate.select()
                .where(ThoughtTemplate.name == template_name)
                .exists()
            ):
                raise ValueError("Template name already exists")
            ThoughtTemplate.create(
                name=template_name,
                content=template_content,
            )
            print(f"Thought template '{template_name}' added.")
            return True

    def get_thought_template(self, template_name):
        try:
            return ThoughtTemplate.get(ThoughtTemplate.name == template_name)
        except ThoughtTemplate.DoesNotExist:
            return None

    def update_thought_template(self, template_name, template_content):
        with db.atomic():
            template = ThoughtTemplate.get(ThoughtTemplate.name == template_name)
            template.content = template_content
            template.save()
            print(f"Thought template '{template_name}' updated.")
            return True

    def delete_thought_template(self, template_name):
        with db.atomic():
            query = ThoughtTemplate.delete().where(
                ThoughtTemplate.name == template_name
            )
            return query.execute()

    def get_thought_template_names(self):
        return [template.name for template in ThoughtTemplate.select()]

    def get_thought_template_inputs_outputs(self, template_content):
        return self.thought_engine.get_thought_template_inputs_outputs(template_content)

    def execute_template(
        self, agent, content, inputs, outputs, partial_execution=False
    ):
        return self.thought_engine.execute_template(
            agent, content, inputs, outputs, partial_execution=partial_execution
        )
