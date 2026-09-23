from src.notes import NotesStore


def test_add_and_list_notes():
    store = NotesStore()
    store.add("alpha")
    store.add("beta")
    assert store.list_notes() == ["alpha", "beta"]
