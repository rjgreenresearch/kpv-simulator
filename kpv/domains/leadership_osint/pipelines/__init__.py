from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = BASE_DIR / "schemas"
DATA_DIR = BASE_DIR / "data"


def load_schema(name: str) -> dict:
    """
    Load a JSON schema by name (person, organization, edge).
    """
    schema_path = SCHEMAS_DIR / f"{name}.schema.json"
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_country_data(country_code: str):
    """
    Load persons, organizations, and edges for a given country.
    """
    cc = country_code.lower()
    country_dir = DATA_DIR / cc

    persons = json.loads((country_dir / "persons.json").read_text(encoding="utf-8"))
    orgs = json.loads((country_dir / "organizations.json").read_text(encoding="utf-8"))
    edges = json.loads((country_dir / "edges.json").read_text(encoding="utf-8"))

    return persons, orgs, edges


def build_country_graph(core_graph_cls, country_code: str):
    """
    Construct a KPV graph instance populated with leadership OSINT data
    for a specific country.
    """
    persons, orgs, edges = load_country_data(country_code)

    graph = core_graph_cls()

    # TODO: integrate with your core node/edge models
    # graph.add_person_nodes(persons)
    # graph.add_org_nodes(orgs)
    # graph.add_edges(edges)

    return graph

