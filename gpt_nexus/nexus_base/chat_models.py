from enum import Enum

from peewee import (
    SQL,
    AutoField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

db = SqliteDatabase("nexus.db")


class BaseModel(Model):
    class Meta:
        database = db


class ChatParticipants(BaseModel):
    user_id = CharField(primary_key=True)
    username = CharField(unique=True)
    display_name = CharField()
    participant_type = CharField()  # Consider using Enum in a real system
    email = CharField(null=True)
    password_hash = CharField(null=True)
    status = CharField()  # Active, Inactive, Suspended
    profile_icon = CharField(null=True)
    avatar = CharField(null=True)
    timestamp = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "participant_type": self.participant_type,
            "email": self.email,
            "status": self.status,
            "profile_icon": self.profile_icon,
            "avatar": self.avatar,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Thread(BaseModel):
    thread_id = AutoField()
    title = CharField(unique=True)
    timestamp = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    def to_dict(self):
        return {
            "thread_id": self.thread_id,
            "title": self.title,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Message(BaseModel):
    thread = ForeignKeyField(Thread, backref="messages")
    author = ForeignKeyField(ChatParticipants, backref="messages")
    role = CharField()  # user, agent, system
    content = TextField()
    timestamp = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    def to_dict(self):
        return {
            "thread_id": self.thread.thread_id,
            "author": self.author.username,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Subscriber(BaseModel):
    participant = ForeignKeyField(ChatParticipants, backref="subscriptions")
    thread = ForeignKeyField(Thread, backref="subscribers")
    timestamp = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])


class Notification(BaseModel):
    participant = ForeignKeyField(ChatParticipants, backref="notifications")
    thread = ForeignKeyField(Thread)
    message = ForeignKeyField(Message)
    timestamp = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])


class KnowledgeStore(BaseModel):
    name = CharField(unique=True)

    chunking_option = CharField(default="Character")
    chunk_size = IntegerField(default=512)
    overlap = IntegerField(default=128)


class MemoryType(Enum):
    CONVERSATIONAL = "CONVERSATIONAL"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    EPISODIC = "EPISODIC"


class MemoryFunction(BaseModel):
    memory_type = CharField(
        choices=[(m.value, m.name) for m in MemoryType],
        default=MemoryType.CONVERSATIONAL.value,
    )
    function_prompt = TextField()
    function_keys = CharField()
    augmentation_prompt = TextField(null=True)
    augmentation_keys = CharField(null=True)
    summarization_prompt = TextField(null=True)


class MemoryStore(BaseModel):
    name = CharField(unique=True)
    memory_type = CharField(
        choices=[(m.value, m.name) for m in MemoryType],
        default=MemoryType.CONVERSATIONAL.value,
    )


class Document(BaseModel):
    store = ForeignKeyField(KnowledgeStore, backref="documents")
    name = CharField()


class PromptTemplate(BaseModel):
    name = CharField(unique=True)
    content = TextField()


def initialize_db():
    db.connect()
    db.create_tables(
        [
            ChatParticipants,
            Thread,
            Message,
            Subscriber,
            Notification,
            KnowledgeStore,
            Document,
            PromptTemplate,
            MemoryStore,
            MemoryFunction,
        ],
        safe=True,
    )

    # Add some initial data
    if (
        not MemoryFunction.select()
        .where(MemoryFunction.memory_type == MemoryType.CONVERSATIONAL.value)
        .exists()
    ):
        MemoryFunction.create(
            memory_type=MemoryType.CONVERSATIONAL.value,
            function_prompt="Summarize the conversation and create a set of statements that summarize the conversation. Return a JSON object with the following keys: 'summary'. Each key should have a list of statements that are relevant to that category. Return only the JSON object and nothing else.",
            function_keys="summary",
            summarization_prompt="Given a conversation transcript, synthesize the key points, themes, and takeaways into a concise summary. Focus on the main ideas, important details, and any conclusions or insights that emerged during the conversation. The summary should capture the essence of the discussion and provide a clear, coherent overview of the main topics covered. Avoid unnecessary repetition or irrelevant information, and aim to distill the conversation into a few key points that highlight the most important aspects of the interaction.",
        )

    if (
        not MemoryFunction.select()
        .where(MemoryFunction.memory_type == MemoryType.SEMANTIC.value)
        .exists()
    ):
        MemoryFunction.create(
            memory_type=MemoryType.SEMANTIC.value,
            function_prompt="Summarize the facts and preferences in the conversation. Return a JSON object with the following keys: 'questions', 'facts', 'preferences'. Each key should have a list of statements that are relevant to that category. Return only the JSON object and nothing else.",
            function_keys="questions,facts,preferences",
            augmentation_prompt="Generate a set of questions that can be asked based on the conversation. Return a JSON object with the following keys: 'questions'. Each key should have a list of questions that can be asked based on the conversation. Return only the JSON object and nothing else.",
            augmentation_keys="questions",
            summarization_prompt="Given a list of personal memories described below, synthesize these into a concise narrative that captures their essence, emotional significance, and any common themes. Focus on the underlying feelings, lessons learned, or how these memories collectively shape my understanding of a particular aspect of my life. Please merge similar memories and emphasize unique insights or moments of growth. The aim is to create a compact, meaningful representation of these experiences that reflects their impact on me rather than a detailed account of each memory",
        )

    if (
        not MemoryFunction.select()
        .where(MemoryFunction.memory_type == MemoryType.PROCEDURAL.value)
        .exists()
    ):
        MemoryFunction.create(
            memory_type=MemoryType.PROCEDURAL.value,
            function_prompt="Summarize all the tasks, steps and procedures that are identified in the conversation. Return a JSON object with the following keys: 'tasks', 'steps', 'procedures'. Each key should have a list of statements that are relevant to that category. Return only the JSON object and nothing else.",
            function_keys="tasks,steps,procedures",
            augmentation_prompt="Generate a set of tasks that need to be completed based on the conversation. Return a JSON object with the following keys: 'tasks'. Each key should have a list of tasks that need to be completed based on the conversation. Return only the JSON object and nothing else.",
            augmentation_keys="tasks",
            summarization_prompt="Given a list of tasks described below, synthesize these into a concise narrative that captures their essence, emotional significance, and any common themes. Focus on the underlying feelings, lessons learned, or how these tasks collectively shape my understanding of a particular aspect of the problem. Please merge similar tasks and emphasize unique insights or moments of growth. The aim is to create a compact, meaningful representation of these experiences that reflects their impact on the problem rather than a detailed account of each task",
        )

    if (
        not MemoryFunction.select()
        .where(MemoryFunction.memory_type == MemoryType.EPISODIC.value)
        .exists()
    ):
        MemoryFunction.create(
            memory_type=MemoryType.EPISODIC.value,
            function_prompt="Extract all the events and episodes that are identified in the conversation. Return a JSON object with the following keys: 'events', 'episodes'. Each key should have a list of statements that are relevant to that category. Return only the JSON object and nothing else.",
            function_keys="events,episodes",
            augmentation_prompt="Generate a set of events that have occurred based on the conversation. Return a JSON object with the following keys: 'events'. Each key should have a list of events that have occurred based on the conversation. Return only the JSON object and nothing else.",
            augmentation_keys="events",
            summarization_prompt="Given a list of events described below, synthesize these into a concise narrative that captures their essence, emotional significance, and any common themes. Focus on the underlying feelings, lessons learned, or how these events collectively shape my understanding of a particular aspect of a problem. Please merge similar events and emphasize unique insights or moments of growth. The aim is to create a compact, meaningful representation of these experiences that reflects their impact on me rather than a detailed account of each event",
        )

    if not PromptTemplate.select().where(PromptTemplate.name == "reasoning").exists():
        PromptTemplate.create(
            name="reasoning",
            content="""
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
            """,
        )

    if not PromptTemplate.select().where(PromptTemplate.name == "evaluation").exists():
        PromptTemplate.create(
            name="evaluation",
            content="""
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
            """,
        )

    if (
        not PromptTemplate.select()
        .where(PromptTemplate.name == "reasoning_evaluation")
        .exists()
    ):
        PromptTemplate.create(
            name="reasoning_evaluation",
            content="""
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
                    Summarize how well the problem was solved given the following evaluation
                    evaluation: {{>evaluation input output}}
            """,
        )

    if (
        not PromptTemplate.select()
        .where(PromptTemplate.name == "simple_template")
        .exists()
    ):
        PromptTemplate.create(
            name="simple_template",
            content="""
            inputs:
                type: prompt
                input:
                    type: string
                template: |
                    {{#augment input}}

                outputs:
                type: function
                output:
                    type: string
                template: |
                    {{>format output}}

                helpers:
                # Defines a method to augment the knowledge of the input
                augment: |
                    def augment(this, aug):
                        return "Augment the prompt: " + aug
                            """,
        )

    if not PromptTemplate.select().where(PromptTemplate.name == "format").exists():
        PromptTemplate.create(
            name="format",
            content="""
            inputs:
                type: function
                input:
                    type: string
                template: |
                    {{#format input}}

                helpers:
                # Defines a method to augment the knowledge of the input
                    format: |
                        def format(this, aug):
                            return aug.upper()
                    """,
        )

    if not PromptTemplate.select().where(PromptTemplate.name == "header").exists():
        PromptTemplate.create(
            name="header",
            content="""
                inputs:
                    type: function
                    input:
                        type: string
                    template: |
                        {{#header input}}
                    helpers:
                        header: |
                            def header(arg):
                                return arg.upper()
                    """,
        )

    if not PromptTemplate.select().where(PromptTemplate.name == "base_agent").exists():
        PromptTemplate.create(
            name="base_agent",
            content="""
            inputs:
                type: prompt
                input:
                    type: string
                template: |
                    {{>header input}}
                    
                    {{#augment_memory input}}
                    
                    {{#augment_knowledge input}}

                outputs:
                    type: function
                    output:
                        type: string
                    template: "{{#format output}}"

                helpers:
                    # Defines a method to augment the memory of the input
                    augment_memory: |
                        def augment_memory(this, arg):
                            aug = arg
                            if agent.memory_store:
                                aug = nexus.apply_memory_RAG(agent.memory_store, arg, agent)
                            return aug
                        
                    # Defines a method to augment the knowledge of the input
                    augment_knowledge: |
                        def augment_knowledge(this, arg):
                            aug = arg
                            if agent.knowledge_store:
                                aug = nexus.apply_knowledge_RAG(agent.knowledge_store, arg)
                            return aug
                        
                    # Modifies the response to uppercase
                    format: |
                        def format(response):
                            return response.upper()

                        """,
        )


initialize_db()
