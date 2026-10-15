"""Independent reachability oracle: plain Python DFS over the fixture, no database."""


def routes(fixture, identity, resource, cut=()):
    """Every route from identity to resource as a sorted list of edge-id tuples."""
    adj = {}
    for e in fixture["edges"]:
        if e["enabled"] and e["id"] not in cut:
            adj.setdefault(e["src"], []).append(e)
    out = []

    def walk(node, trail):
        for e in adj.get(node, []):
            if e["dst"] == resource and e["type"] == "GRANTS_ACCESS":
                out.append(tuple(trail + [e["id"]]))
            elif e["type"] != "GRANTS_ACCESS":
                walk(e["dst"], trail + [e["id"]])

    walk(identity, [])
    return sorted(out)
