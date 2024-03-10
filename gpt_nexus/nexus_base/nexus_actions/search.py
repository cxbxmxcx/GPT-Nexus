import wikipedia

from gpt_nexus.nexus_base.action_manager import agent_action


@agent_action
def search_wikipedia(query):
    """Searches Wikipedia for the given query and returns the page search results."""
    wikipedia.set_lang("en")
    search_results = wikipedia.search(query)
    return search_results


@agent_action
def get_wikipedia_summary(query):
    """Gets the summary of the Wikipedia page for the given page."""
    wikipedia.set_lang("en")
    summary = wikipedia.summary(query)
    return summary


@agent_action
def get_wikipedia_page(query):
    """Gets the full content of the Wikipedia page for the given page query."""
    wikipedia.set_lang("en")
    page = wikipedia.page(query)
    return page.content
