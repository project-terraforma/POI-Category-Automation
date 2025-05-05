import ast
import json

def build_category_tree(path_to_txt):
    tree = {}
    with open(path_to_txt, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ';' not in line or '[' not in line or ']' not in line:
                continue
            _, raw = line.split(';', 1)
            start = raw.find('[')
            end   = raw.rfind(']')
            if start < 0 or end < 0:
                continue
            parts = [p.strip() for p in raw[start+1:end].split(',') if p.strip()]
            node = tree
            for key in parts:
                node = node.setdefault(key, {})
    return tree

# 1. Build the tree
tree = build_category_tree("Data/categories.txt")

# 2. Write full tree to JSON
with open("category_tree.json", "w", encoding="utf-8") as out:
    json.dump(tree, out, indent=2, ensure_ascii=False)

print(f"Wrote category_tree.json with {len(tree)} top-level entries.")
