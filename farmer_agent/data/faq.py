# Offline FAQ & Guidance
# Provides frequently asked questions and best practices for common crops/issues
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
FAQ_FILE = os.path.join(DATA_DIR, 'faq.json')

class FAQ:
    def __init__(self):
        self.faq = self.load_faq()

    def load_faq(self):
        if not os.path.exists(FAQ_FILE):
            return []
        with open(FAQ_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search(self, query, tags=None, fuzzy=False, use_llm=True, model="phi3:mini", host="http://localhost:11434"):
        """
        Search FAQ using local LLM (Ollama) if available, otherwise fallback to static FAQ search.
        :param query: search string
        :param tags: list of tags/categories to filter (optional)
        :param fuzzy: if True, allow partial/fuzzy match
        :param use_llm: if True, use Ollama LLM for response
        :param model: Ollama model name
        :param host: Ollama server host
        """
        if use_llm:
            try:
                import requests
                url = f"{host}/api/generate"
                payload = {
                    "model": model,
                    "prompt": query,
                    "stream": False
                }
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
                llm_response = response.json().get("response", "")
                return [{"question": query, "answer": llm_response, "tags": ["llm"]}]
            except Exception as e:
                # Fallback to static search if LLM fails
                pass
        # --- Static search fallback ---
        import difflib
        query_l = query.lower()
        results = []
        for item in self.faq:
            q = item.get('question', '').lower()
            a = item.get('answer', '').lower()
            item_tags = [t.lower() for t in item.get('tags', [])] if 'tags' in item else []
            match = False
            if fuzzy:
                if difflib.get_close_matches(query_l, [q, a], n=1, cutoff=0.6):
                    match = True
            else:
                if query_l in q or query_l in a:
                    match = True
            if match:
                if tags:
                    if any(tag.lower() in item_tags for tag in tags):
                        results.append(item)
                else:
                    results.append(item)
        return results

    def related_questions(self, query, top_n=3):
        """
        Return top N related questions using fuzzy matching.
        """
        import difflib
        questions = [item['question'] for item in self.faq]
        matches = difflib.get_close_matches(query, questions, n=top_n, cutoff=0.4)
        return [item for item in self.faq if item['question'] in matches]

    def get_all(self):
        return self.faq

if __name__ == "__main__":
    faq = FAQ()
    print(faq.get_all())
    print(faq.search('tomato'))
