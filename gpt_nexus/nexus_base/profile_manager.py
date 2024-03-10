import os

import yaml


class AgentProfile:
    def __init__(
        self,
        name,
        avatar,
        persona,
        preferred_functions,
        knowledge,
        memory,
        planners,
        feedback,
    ):
        self.name = name
        self.avatar = None
        self.persona = persona
        self.preferred_functions = preferred_functions
        self.knowledge = knowledge
        self.memory = memory
        self.planners = planners
        self.feedback = feedback


class ProfileManager:
    def __init__(self):
        self.directory = os.path.join(os.path.dirname(__file__), "nexus_profiles")
        self.agent_profiles = []
        self.load_profiles()

    def load_profiles(self):
        # Scan the directory for YAML files
        for filename in os.listdir(self.directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.directory, filename)
                with open(file_path, "r") as file:
                    profile_data = yaml.safe_load(file)
                    self.create_agent_profile(profile_data)

    def create_agent_profile(self, profile_data):
        if "agentProfile" in profile_data:
            profile = profile_data["agentProfile"]
            agent = AgentProfile(
                name=profile.get("name", ""),
                avatar=profile.get("avatar", ""),
                persona=profile.get("persona", ""),
                preferred_functions=profile.get("preferredFunctions", []),
                knowledge=profile.get("knowledge", None),
                memory=profile.get("memory", None),
                planners=profile.get("planners", None),
                feedback=profile.get("feedback", None),
            )
            self.agent_profiles.append(agent)

    def get_agent_profile(self, profile_name):
        for profile in self.agent_profiles:
            if profile.name == profile_name:
                return profile
        return None

    def get_agent_profile_names(self):
        return [profile.name for profile in self.agent_profiles]


# # Usage
# if __name__ == "__main__":
#     manager = ProfileManager()
#     for profile in manager.agent_profiles:
#         print(profile.persona, profile.preferred_functions)
