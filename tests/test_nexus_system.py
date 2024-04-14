import pytest

from gpt_nexus.nexus_base.chat_system import ChatSystem


@pytest.fixture
def nexus():
    # Create an instance of ChatSystem for testing
    return ChatSystem()


def test_nexus_get_all_participants(nexus):
    # Test the get_all_participants method
    users = nexus.get_all_participants()
    assert len(users) > 0
