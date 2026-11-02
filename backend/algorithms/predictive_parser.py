
try:
    from .grammar import parse_grammar
    from .parsing_table import generate_ll1_table
except ImportError:
    from grammar import parse_grammar
    from parsing_table import generate_ll1_table


END_MARKER = "$"
EPSILON = "ε"


# -------------------------------------------------
# TOKENIZE INPUT STRING
# -------------------------------------------------

def tokenize_input(input_string, terminals):

    text = input_string.strip()

    tokens = []
    position = 0

    # Match longer terminals first
    sorted_terminals = sorted(
        terminals,
        key=len,
        reverse=True
    )

    while position < len(text):

        if text[position].isspace():
            position += 1
            continue

        matched = False

        for terminal in sorted_terminals:

            if text.startswith(terminal, position):

                tokens.append(terminal)
                position += len(terminal)
                matched = True
                break

        if not matched:

            return None, position, text[position]

    return tokens, None, None


# -------------------------------------------------
# CREATE PARSE TREE NODE
# -------------------------------------------------

def create_node(symbol):

    return {
        "symbol": symbol,
        "children": []
    }


# -------------------------------------------------
# DISPLAY STACK
# -------------------------------------------------

def format_stack(stack):

    symbols = [
        symbol
        for symbol, node in reversed(stack)
    ]

    return " ".join(symbols)


# -------------------------------------------------
# PREDICTIVE PARSING
# -------------------------------------------------

def predictive_parse(grammar_text, input_string):

    # Validate grammar
    grammar_result = parse_grammar(grammar_text)

    if not grammar_result["valid"]:

        return {
            "valid": False,
            "is_ll1": False,
            "accepted": False,
            "trace": [],
            "parse_tree": None,
            "error": grammar_result["errors"],
            "error_position": None
        }

    # Generate LL(1) parsing table
    table_result = generate_ll1_table(grammar_text)

    if not table_result["valid"]:

        return {
            "valid": False,
            "is_ll1": False,
            "accepted": False,
            "trace": [],
            "parse_tree": None,
            "error": table_result["errors"],
            "error_position": None
        }

    # Check for LL(1) conflicts
    if not table_result["is_ll1"]:

        return {
            "valid": True,
            "is_ll1": False,
            "accepted": False,
            "trace": [],
            "parse_tree": None,
            "error": [
                "Grammar is not LL(1). "
                "Resolve parsing table conflicts first."
            ],
            "conflicts": table_result["conflicts"],
            "error_position": None
        }

    productions = grammar_result["productions"]

    non_terminals = set(
        grammar_result["non_terminals"]
    )

    terminals = set(
        grammar_result["terminals"]
    )

    start_symbol = grammar_result["start_symbol"]

    parsing_table = table_result["table"]

    # Tokenize input
    tokens, error_position, invalid_symbol = tokenize_input(
        input_string,
        terminals
    )

    if tokens is None:

        return {
            "valid": True,
            "is_ll1": True,
            "accepted": False,
            "tokens": [],
            "trace": [],
            "parse_tree": None,
            "error": [
                f"Invalid input symbol '{invalid_symbol}'."
            ],
            "error_position": error_position
        }

    # Add end marker
    tokens.append(END_MARKER)

    # ---------------------------------------------
    # INITIALIZE STACK AND TREE
    # ---------------------------------------------

    root = create_node(start_symbol)

    stack = [
        (END_MARKER, None),
        (start_symbol, root)
    ]

    position = 0
    trace = []
    accepted = False

    # Safety limit
    max_steps = max(
        100,
        len(tokens) * 50
    )

    # ---------------------------------------------
    # PARSING LOOP
    # ---------------------------------------------

    for step in range(1, max_steps + 1):

        if not stack:
            break

        stack_before = format_stack(stack)

        remaining_input = " ".join(
            tokens[position:]
        )

        top_symbol, current_node = stack[-1]

        lookahead = tokens[position]

        # -----------------------------------------
        # ACCEPTANCE CONDITION
        # -----------------------------------------

        if (
            top_symbol == END_MARKER
            and lookahead == END_MARKER
        ):

            stack.pop()

            trace.append({

                "step": step,

                "stack": stack_before,

                "remaining_input": remaining_input,

                "action": "Accept"

            })

            accepted = True
            break

        # -----------------------------------------
        # TERMINAL MATCHING
        # -----------------------------------------

        if (
            top_symbol not in non_terminals
            and top_symbol == lookahead
        ):

            trace.append({

                "step": step,

                "stack": stack_before,

                "remaining_input": remaining_input,

                "action": f"Match '{lookahead}'"

            })

            stack.pop()
            position += 1

            continue

        # -----------------------------------------
        # TERMINAL MISMATCH
        # -----------------------------------------

        if top_symbol not in non_terminals:

            trace.append({

                "step": step,

                "stack": stack_before,

                "remaining_input": remaining_input,

                "action": (
                    f"Error: Expected '{top_symbol}' "
                    f"but found '{lookahead}'"
                )

            })

            return {

                "valid": True,
                "is_ll1": True,
                "accepted": False,
                "tokens": tokens[:-1],
                "trace": trace,
                "parse_tree": None,
                "error": [
                    f"Expected '{top_symbol}' "
                    f"but found '{lookahead}'."
                ],
                "error_position": position

            }

        # -----------------------------------------
        # NON-TERMINAL: LOOK UP TABLE ENTRY
        # -----------------------------------------

        cell = parsing_table.get(
            top_symbol,
            {}
        ).get(
            lookahead,
            []
        )

        if not cell:

            trace.append({

                "step": step,

                "stack": stack_before,

                "remaining_input": remaining_input,

                "action": (
                    f"Error: No production for "
                    f"M[{top_symbol}, {lookahead}]"
                )

            })

            expected = [

                terminal

                for terminal, entries
                in parsing_table[top_symbol].items()

                if entries

            ]

            return {

                "valid": True,
                "is_ll1": True,
                "accepted": False,
                "tokens": tokens[:-1],
                "trace": trace,
                "parse_tree": None,
                "error": [
                    f"No production found for "
                    f"M[{top_symbol}, {lookahead}]."
                ],
                "expected": expected,
                "error_position": position

            }

        # One production is expected in LL(1)
        entry = cell[0]

        production = entry["production"]

        rhs = entry["rhs"]

        # -----------------------------------------
        # APPLY PRODUCTION
        # -----------------------------------------

        trace.append({

            "step": step,

            "stack": stack_before,

            "remaining_input": remaining_input,

            "action": f"Apply {production}"

        })

        stack.pop()

        # -----------------------------------------
        # EPSILON PRODUCTION
        # -----------------------------------------

        if not rhs:

            epsilon_node = create_node(EPSILON)

            current_node["children"].append(
                epsilon_node
            )

            continue

        # -----------------------------------------
        # CREATE CHILD NODES
        # -----------------------------------------

        children = []

        for symbol in rhs:

            child = create_node(symbol)

            children.append(child)

            current_node["children"].append(
                child
            )

        # Push RHS symbols in reverse order
        for symbol, child in reversed(
            list(zip(rhs, children))
        ):

            stack.append(
                (symbol, child)
            )

    # ---------------------------------------------
    # STEP LIMIT
    # ---------------------------------------------

    if not accepted:

        if len(trace) >= max_steps:

            error_message = (
                "Parsing stopped because the maximum "
                "number of steps was reached."
            )

        else:

            error_message = (
                "Input could not be accepted."
            )

        return {

            "valid": True,
            "is_ll1": True,
            "accepted": False,
            "tokens": tokens[:-1],
            "trace": trace,
            "parse_tree": None,
            "error": [error_message],
            "error_position": position

        }

    # ---------------------------------------------
    # SUCCESSFUL RESULT
    # ---------------------------------------------

    return {

        "valid": True,

        "is_ll1": True,

        "accepted": True,

        "tokens": tokens[:-1],

        "trace": trace,

        "parse_tree": root,

        "error": [],

        "error_position": None

    }


# -------------------------------------------------
# DISPLAY PARSING TRACE
# -------------------------------------------------

def display_trace(result):

    if not result["valid"]:

        print("\nInvalid grammar.")

        for error in result["error"]:
            print(error)

        return

    if not result["is_ll1"]:

        print("\nGrammar is NOT LL(1).")

        for error in result["error"]:
            print(error)

        return

    print("\nPREDICTIVE PARSING TRACE")
    print("=" * 95)

    print(
        f"{'Step':<8}"
        f"{'Stack':<28}"
        f"{'Remaining Input':<35}"
        f"{'Action'}"
    )

    print("-" * 95)

    for item in result["trace"]:

        print(
            f"{item['step']:<8}"
            f"{item['stack']:<28}"
            f"{item['remaining_input']:<35}"
            f"{item['action']}"
        )

    print("-" * 95)

    if result["accepted"]:

        print("\nInput string ACCEPTED!")

    else:

        print("\nInput string REJECTED!")

        for error in result["error"]:
            print(error)


# -------------------------------------------------
# TEST THE MODULE
# -------------------------------------------------

if __name__ == "__main__":

    test_grammar = """
E->TE'
E'->+TE'|epsilon
T->FT'
T'->*FT'|epsilon
F->(E)|id
"""

    test_input = "id+id*id"

    result = predictive_parse(
        test_grammar,
        test_input
    )

    display_trace(result)

    if result["accepted"]:

        print("\nParse Tree generated successfully!")

    else:

        print("\nNo valid parse tree generated.")
