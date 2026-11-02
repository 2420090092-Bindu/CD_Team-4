
try:
    from .grammar import parse_grammar
    from .first_follow import calculate_first_follow
except ImportError:
    from grammar import parse_grammar
    from first_follow import calculate_first_follow


EPSILON = "ε"
END_MARKER = "$"


# -------------------------------------------------
# FORMAT PRODUCTION
# -------------------------------------------------

def format_production(lhs, rhs):

    if not rhs:
        return f"{lhs} -> {EPSILON}"

    return f"{lhs} -> {''.join(rhs)}"


# -------------------------------------------------
# FIND FIRST OF A PRODUCTION RHS
# -------------------------------------------------

def first_of_rhs(rhs, first_sets, non_terminals):

    result = set()

    if not rhs:
        return {EPSILON}

    all_nullable = True

    for symbol in rhs:

        # Non-terminal
        if symbol in non_terminals:

            result.update(
                set(first_sets[symbol]) - {EPSILON}
            )

            if EPSILON in first_sets[symbol]:
                continue

            all_nullable = False
            break

        # Terminal
        else:

            result.add(symbol)
            all_nullable = False
            break

    if all_nullable:
        result.add(EPSILON)

    return result


# -------------------------------------------------
# GENERATE LL(1) PARSING TABLE
# -------------------------------------------------

def generate_ll1_table(grammar_text):

    # Validate grammar
    grammar_result = parse_grammar(grammar_text)

    if not grammar_result["valid"]:

        return {
            "valid": False,
            "is_ll1": False,
            "errors": grammar_result["errors"],
            "rows": [],
            "columns": [],
            "table": {},
            "conflicts": [],
            "error_entries": [],
            "steps": []
        }

    # Calculate FIRST and FOLLOW
    analysis = calculate_first_follow(grammar_text)

    if not analysis["valid"]:

        return {
            "valid": False,
            "is_ll1": False,
            "errors": analysis["errors"],
            "rows": [],
            "columns": [],
            "table": {},
            "conflicts": [],
            "error_entries": [],
            "steps": []
        }

    productions = grammar_result["productions"]

    non_terminals = set(
        grammar_result["non_terminals"]
    )

    first_sets = analysis["first"]

    follow_sets = analysis["follow"]

    # ---------------------------------------------
    # CREATE TABLE ROWS AND COLUMNS
    # ---------------------------------------------

    rows = sorted(non_terminals)

    columns = sorted(
        set(grammar_result["terminals"])
    )

    # End marker is the final column
    columns.append(END_MARKER)

    # Initialize every cell as empty
    table = {

        nt: {
            terminal: []
            for terminal in columns
        }

        for nt in rows

    }

    steps = []
    conflicts = []

    # ---------------------------------------------
    # PROCESS EVERY PRODUCTION
    # ---------------------------------------------

    for lhs, alternatives in productions.items():

        for rhs in alternatives:

            production_text = format_production(
                lhs, rhs
            )

            rhs_first = first_of_rhs(
                rhs,
                first_sets,
                non_terminals
            )

            steps.append(
                f"Processing {production_text}"
            )

            # FIRST(rhs) without epsilon
            lookaheads = (
                rhs_first - {EPSILON}
            )

            # Add FOLLOW(lhs) if epsilon is possible
            if EPSILON in rhs_first:

                steps.append(
                    f"Since {production_text} can derive epsilon, "
                    f"add FOLLOW({lhs}) to its parsing table entries."
                )

                lookaheads.update(
                    follow_sets[lhs]
                )

            # -------------------------------------
            # FILL TABLE CELLS
            # -------------------------------------

            for terminal in sorted(lookaheads):

                if terminal not in table[lhs]:
                    continue

                entry = {
                    "production": production_text,
                    "lhs": lhs,
                    "rhs": rhs
                }

                table[lhs][terminal].append(entry)

                steps.append(
                    f"M[{lhs}, {terminal}] = {production_text}"
                )

    # ---------------------------------------------
    # DETECT CONFLICTS
    # ---------------------------------------------

    for lhs in rows:

        for terminal in columns:

            cell = table[lhs][terminal]

            # More than one production in a cell
            if len(cell) > 1:

                conflicts.append({

                    "non_terminal": lhs,

                    "lookahead": terminal,

                    "productions": [
                        item["production"]
                        for item in cell
                    ]

                })

    # ---------------------------------------------
    # IDENTIFY EMPTY / ERROR ENTRIES
    # ---------------------------------------------

    error_entries = []

    for lhs in rows:

        for terminal in columns:

            if not table[lhs][terminal]:

                error_entries.append({

                    "non_terminal": lhs,

                    "lookahead": terminal,

                    "status": "ERROR"

                })

    # ---------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------

    return {

        "valid": True,

        "is_ll1": len(conflicts) == 0,

        "start_symbol": analysis["start_symbol"],

        "rows": rows,

        "columns": columns,

        "table": table,

        "conflicts": conflicts,

        "error_entries": error_entries,

        "steps": steps,

        "first": first_sets,

        "follow": follow_sets,

        "errors": []

    }


# -------------------------------------------------
# DISPLAY LL(1) TABLE
# -------------------------------------------------

def display_table(result):

    if not result["valid"]:

        print("Invalid grammar.")

        for error in result["errors"]:
            print(error)

        return

    rows = result["rows"]

    columns = result["columns"]

    table = result["table"]

    print("\nLL(1) PARSING TABLE")
    print("=" * 80)

    print(
        f"{'NON-TERMINAL':<18}",
        end=""
    )

    for terminal in columns:

        print(
            f"{terminal:<18}",
            end=""
        )

    print()

    print("-" * (18 * (len(columns) + 1)))

    for nt in rows:

        print(
            f"{nt:<18}",
            end=""
        )

        for terminal in columns:

            cell = table[nt][terminal]

            if not cell:

                value = "ERROR"

            else:

                value = " / ".join(
                    item["production"]
                    for item in cell
                )

            print(
                f"{value:<18}",
                end=""
            )

        print()

    # ---------------------------------------------
    # DISPLAY CONFLICTS
    # ---------------------------------------------

    print("\nCONFLICT ANALYSIS")
    print("-" * 80)

    if result["conflicts"]:

        print("Grammar is NOT LL(1).")

        for conflict in result["conflicts"]:

            print(
                f"Conflict at M[{conflict['non_terminal']}, "
                f"{conflict['lookahead']}]: "
                f"{conflict['productions']}"
            )

    else:

        print("No conflicts found.")
        print("Grammar is LL(1).")

    print(
        "\nTotal empty/error entries:",
        len(result["error_entries"])
    )


# -------------------------------------------------
# TEST THE MODULE
# -------------------------------------------------

if __name__ == "__main__":

    test_grammar = """
E->TE'
E'->+TE'|ε
T->FT'
T'->*FT'|ε
F->(E)|id
"""

    result = generate_ll1_table(
        test_grammar
    )

    display_table(result)
