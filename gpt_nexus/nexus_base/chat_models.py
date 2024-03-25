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


class MemoryStore(BaseModel):
    name = CharField(unique=True)
    memory_type = CharField(
        choices=[(m.value, m.name) for m in MemoryType],
        default=MemoryType.CONVERSATIONAL.value,
    )


class Document(BaseModel):
    store = ForeignKeyField(KnowledgeStore, backref="documents")
    name = CharField()


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
            MemoryStore,
            MemoryFunction,
        ],
        safe=True,
    )

    # Add some initial data
    MemoryFunction.create(
        memory_type=MemoryType.CONVERSATIONAL.value,
        function_prompt="Summarize the conversation and create a set of statements that summarize the conversation. Return a JSON object with the following keys: 'summary'. Each key should have a list of statements that are relevant to that category.",
        function_keys="summary",
    )
    MemoryFunction.create(
        memory_type=MemoryType.SEMANTIC.value,
        function_prompt="Summarize the facts and preferences in the conversation. Return a JSON object with the following keys: 'questions', 'facts', 'preferences'. Each key should have a list of statements that are relevant to that category.",
        function_keys="questions, facts, preferences",
    )
    MemoryFunction.create(
        memory_type=MemoryType.PROCEDURAL.value,
        function_prompt="Summarize all the tasks, steps and procedures that are identified in the conversation. Return a JSON object with the following keys: 'tasks', 'steps', 'procedures'. Each key should have a list of statements that are relevant to that category.",
        function_keys="tasks, steps, procedures",
    )
    MemoryFunction.create(
        memory_type=MemoryType.EPISODIC.value,
        function_prompt="Extract all the events and episodes that are identified in the conversation. Return a JSON object with the following keys: 'events', 'episodes'. Each key should have a list of statements that are relevant to that category.",
        function_keys="events, episodes",
    )


initialize_db()
