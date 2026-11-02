
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import tempfile
import re
import json

# =========================================================
# PARSEVIZ ALGORITHM IMPORTS
# =========================================================

from algorithms.grammar import parse_grammar as validate_parseviz_grammar
from algorithms.left_recursion import eliminate_immediate_left_recursion
from algorithms.left_factoring import eliminate_left_factoring
from algorithms.first_follow import calculate_first_follow
from algorithms.parsing_table import generate_ll1_table
from algorithms.predictive_parser import predictive_parse


app = Flask(__name__)
CORS(app)

COMPILER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "compiler"
)

MAX_PARSE_TREES = 20


# =========================================================
# ORIGINAL CFG ANALYZER
# TOKENIZE GRAMMAR SYMBOLS
# =========================================================

def tokenize(text):

    text = text.replace(" ", "")

    return re.findall(
        r"[A-Z]|[a-z][a-z0-9_]*|.",
        text
    )


# =========================================================
# ORIGINAL CFG ANALYZER
# TOKENIZE INPUT USING GRAMMAR TERMINALS
# =========================================================

def tokenize_input(text, terminal_symbols):

    text = text.replace(" ", "")

    if not text:
        return []

    terminals = sorted(
        terminal_symbols,
        key=len,
        reverse=True
    )

    tokens = []
    position = 0

    while position < len(text):

        matched = False

        for terminal in terminals:

            if text.startswith(terminal, position):

                tokens.append(terminal)
                position += len(terminal)
                matched = True
                break

        if not matched:
            return None

    return tokens


# =========================================================
# ORIGINAL CFG ANALYZER
# READ CFG GRAMMAR
# =========================================================

def parse_grammar(grammar):

    productions = {}
    non_terminals = set()

    for line in grammar.splitlines():

        line = line.strip()

        if not line or "->" not in line:
            continue

        lhs, rhs_part = line.split("->", 1)

        lhs = lhs.strip()

        if not lhs:
            continue

        non_terminals.add(lhs)

        if lhs not in productions:
            productions[lhs] = []

        alternatives = rhs_part.split("|")

        for alternative in alternatives:

            symbols = tokenize(alternative.strip())

            productions[lhs].append(symbols)

    return productions, non_terminals


# =========================================================
# ORIGINAL CFG ANALYZER
# FIND ALL POSSIBLE PARSE TREES
# =========================================================

def find_parse_trees(
    grammar,
    input_string,
    max_trees=MAX_PARSE_TREES
):

    productions, non_terminals = parse_grammar(grammar)

    terminal_symbols = set()

    for lhs, rhs_list in productions.items():

        for rhs in rhs_list:

            for symbol in rhs:

                if symbol not in non_terminals:
                    terminal_symbols.add(symbol)

    target = tokenize_input(
        input_string,
        terminal_symbols
    )

    if target is None:
        return []

    if not productions or not target:
        return []

    start_symbol = next(iter(productions))

    symbol_cache = {}
    sequence_cache = {}
    active_symbols = set()

    # -----------------------------------------------------
    # PARSE A NON-TERMINAL
    # -----------------------------------------------------

    def parse_symbol(symbol, start, end):

        key = (symbol, start, end)

        if key in symbol_cache:
            return symbol_cache[key]

        if key in active_symbols:
            return []

        if start >= end:
            return []

        active_symbols.add(key)

        trees = []
        seen = set()

        try:

            for rhs in productions.get(symbol, []):

                matches = match_sequence(
                    tuple(rhs),
                    start,
                    end
                )

                for children in matches:

                    node = {
                        "symbol": symbol,
                        "children": children
                    }

                    tree_key = json.dumps(
                        node,
                        sort_keys=True
                    )

                    if tree_key not in seen:

                        seen.add(tree_key)
                        trees.append(node)

                    if len(trees) >= max_trees:
                        break

                if len(trees) >= max_trees:
                    break

            symbol_cache[key] = trees

            return trees

        finally:

            active_symbols.remove(key)

    # -----------------------------------------------------
    # MATCH RHS OF A PRODUCTION
    # -----------------------------------------------------

    def match_sequence(rhs, start, end):

        cache_key = (rhs, start, end)

        if cache_key in sequence_cache:
            return sequence_cache[cache_key]

        results = []

        def recurse(index, position, children):

            if len(results) >= max_trees:
                return

            if index == len(rhs):

                if position == end:
                    results.append(children)

                return

            symbol = rhs[index]

            remaining_symbols = len(rhs) - index - 1

            # TERMINAL
            if symbol not in non_terminals:

                if (
                    position < end
                    and target[position] == symbol
                ):

                    child = {
                        "symbol": symbol,
                        "children": []
                    }

                    recurse(
                        index + 1,
                        position + 1,
                        children + [child]
                    )

                return

            # NON-TERMINAL
            max_middle = end - remaining_symbols

            for middle in range(
                position + 1,
                max_middle + 1
            ):

                subtrees = parse_symbol(
                    symbol,
                    position,
                    middle
                )

                for subtree in subtrees:

                    recurse(
                        index + 1,
                        middle,
                        children + [subtree]
                    )

                    if len(results) >= max_trees:
                        return

        recurse(0, start, [])

        sequence_cache[cache_key] = results

        return results

    # -----------------------------------------------------
    # START PARSING
    # -----------------------------------------------------

    trees = parse_symbol(
        start_symbol,
        0,
        len(target)
    )

    return trees[:max_trees]


# =========================================================
# JSON CONVERSION HELPER
# =========================================================

def make_json_safe(value):

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, set):

        return sorted(value)

    if isinstance(value, (list, tuple)):

        return [
            make_json_safe(item)
            for item in value
        ]

    return value


# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message": "CFG Analyzer Backend is running!"
    })


# =========================================================
# ORIGINAL CFG ANALYZER
# ANALYZE ROUTE
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "No JSON data received"
        }), 400

    grammar = data.get("grammar", "").strip()

    input_string = data.get("input_string", "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    parser_path = os.path.join(
        COMPILER_DIR,
        "cfg_parser.exe"
    )

    if not os.path.exists(parser_path):

        return jsonify({
            "error": "cfg_parser.exe not found"
        }), 500

    temp_path = None

    try:

        # Validate grammar through Lex and Yacc

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        ) as temp:

            temp.write(grammar)

            if not grammar.endswith("\n"):
                temp.write("\n")

            temp_path = temp.name

        command = (
            f'"{parser_path}" '
            f'< "{temp_path}"'
        )

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=COMPILER_DIR
        )

        # Generate parse trees

        parse_trees = []

        if input_string:

            parse_trees = find_parse_trees(
                grammar,
                input_string
            )

        return jsonify({

            "output": result.stdout,

            "error": result.stderr,

            "input_string": input_string,

            "parse_tree_count": len(parse_trees),

            "ambiguous_for_input": len(parse_trees) >= 2,

            "parse_trees": parse_trees
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# =========================================================
# PARSEVIZ 1: GRAMMAR VALIDATION
# =========================================================

@app.route("/parseviz/validate", methods=["POST"])
def parseviz_validate():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    try:

        result = validate_parseviz_grammar(grammar)

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PARSEVIZ 2: LEFT RECURSION ELIMINATION
# =========================================================

@app.route("/parseviz/left-recursion", methods=["POST"])
def parseviz_left_recursion():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    try:

        result = eliminate_immediate_left_recursion(grammar)

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PARSEVIZ 3: LEFT FACTORING
# =========================================================

@app.route("/parseviz/left-factoring", methods=["POST"])
def parseviz_left_factoring():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    try:

        result = eliminate_left_factoring(grammar)

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PARSEVIZ 4: FIRST AND FOLLOW
# =========================================================

@app.route("/parseviz/first-follow", methods=["POST"])
def parseviz_first_follow():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    try:

        result = calculate_first_follow(grammar)

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PARSEVIZ 5: LL(1) PARSING TABLE
# =========================================================

@app.route("/parseviz/parsing-table", methods=["POST"])
def parseviz_parsing_table():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    try:

        result = generate_ll1_table(grammar)

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# PARSEVIZ 6: PREDICTIVE PARSING
# =========================================================

@app.route("/parseviz/parse", methods=["POST"])
def parseviz_parse():

    data = request.get_json(silent=True) or {}

    grammar = (data.get("grammar") or "").strip()

    input_string = data.get("input_string", "")

    if not grammar:

        return jsonify({
            "error": "No grammar provided"
        }), 400

    if not isinstance(input_string, str):

        return jsonify({
            "error": "Input string must be text"
        }), 400

    try:

        result = predictive_parse(
            grammar,
            input_string
        )

        return jsonify(make_json_safe(result))

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
