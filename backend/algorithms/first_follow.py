
try:
    from .grammar import parse_grammar
except ImportError:
    from grammar import parse_grammar


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
# FORMAT SET
# -------------------------------------------------

def format_set(symbols):

    return "{ " + ", ".join(symbols) + " }"


# -------------------------------------------------
# FIND FIRST OF A SEQUENCE
# -------------------------------------------------

def first_of_sequence(sequence, first_sets, non_terminals):

    result = set()

    if not sequence:
        return {EPSILON}

    all_nullable = True

    for symbol in sequence:

        # If symbol is a non-terminal
        if symbol in non_terminals:

            result.update(
                first_sets[symbol] - {EPSILON}
            )

            if EPSILON in first_sets[symbol]:
                continue

            all_nullable = False
            break

        # If symbol is a terminal
        else:

            result.add(symbol)
            all_nullable = False
            break

    if all_nullable:
        result.add(EPSILON)

    return result


# -------------------------------------------------
# COMPUTE FIRST SETS
# -------------------------------------------------

def compute_first_sets(productions, non_terminals):

    first_sets = {
        nt: set()
        for nt in non_terminals
    }

    explanations = {
        nt: []
        for nt in non_terminals
    }

    changed = True

    while changed:

        changed = False

        for lhs, alternatives in productions.items():

            for rhs in alternatives:

                production_text = format_production(
                    lhs, rhs
                )

                # Epsilon production
                if not rhs:

                    if EPSILON not in first_sets[lhs]:

                        first_sets[lhs].add(EPSILON)

                        explanations[lhs].append(
                            f"{production_text}: "
                            f"epsilon is added to FIRST({lhs})."
                        )

                        changed = True

                    continue

                all_nullable = True

                for symbol in rhs:

                    # Non-terminal
                    if symbol in non_terminals:

                        new_symbols = (
                            first_sets[symbol] - {EPSILON}
                        )

                        for terminal in sorted(new_symbols):

                            if terminal not in first_sets[lhs]:

                                first_sets[lhs].add(terminal)

                                explanations[lhs].append(
                                    f"{production_text}: "
                                    f"'{terminal}' is added from "
                                    f"FIRST({symbol})."
                                )

                                changed = True

                        if EPSILON in first_sets[symbol]:
                            continue

                        all_nullable = False
                        break

                    # Terminal
                    else:

                        if symbol not in first_sets[lhs]:

                            first_sets[lhs].add(symbol)

                            explanations[lhs].append(
                                f"{production_text}: "
                                f"'{symbol}' is the first terminal."
                            )

                            changed = True

                        all_nullable = False
                        break

                # All symbols can produce epsilon
                if all_nullable:

                    if EPSILON not in first_sets[lhs]:

                        first_sets[lhs].add(EPSILON)

                        explanations[lhs].append(
                            f"{production_text}: "
                            f"all symbols can derive epsilon."
                        )

                        changed = True

    return first_sets, explanations


# -------------------------------------------------
# COMPUTE FOLLOW SETS
# -------------------------------------------------

def compute_follow_sets(
    productions,
    non_terminals,
    first_sets,
    start_symbol
):

    follow_sets = {
        nt: set()
        for nt in non_terminals
    }

    explanations = {
        nt: []
        for nt in non_terminals
    }

    # Add $ to FOLLOW of start symbol
    follow_sets[start_symbol].add(END_MARKER)

    explanations[start_symbol].append(
        f"'{END_MARKER}' is added because "
        f"{start_symbol} is the start symbol."
    )

    changed = True

    while changed:

        changed = False

        for lhs, alternatives in productions.items():

            for rhs in alternatives:

                production_text = format_production(
                    lhs, rhs
                )

                for i, symbol in enumerate(rhs):

                    if symbol not in non_terminals:
                        continue

                    # Get symbols after current non-terminal
                    beta = rhs[i + 1:]

                    # Find FIRST of remaining sequence
                    beta_first = first_of_sequence(
                        beta,
                        first_sets,
                        non_terminals
                    )

                    # ---------------------------------
                    # Rule 1:
                    # Add FIRST(beta) - epsilon
                    # to FOLLOW(symbol)
                    # ---------------------------------

                    new_symbols = beta_first - {EPSILON}

                    for terminal in sorted(new_symbols):

                        if terminal not in follow_sets[symbol]:

                            follow_sets[symbol].add(terminal)

                            explanations[symbol].append(
                                f"{production_text}: "
                                f"'{terminal}' is added from "
                                f"FIRST of the following symbols."
                            )

                            changed = True

                    # ---------------------------------
                    # Rule 2:
                    # If beta is empty or nullable,
                    # add FOLLOW(lhs)
                    # ---------------------------------

                    if EPSILON in beta_first:

                        for terminal in sorted(follow_sets[lhs]):

                            if terminal not in follow_sets[symbol]:

                                follow_sets[symbol].add(terminal)

                                explanations[symbol].append(
                                    f"{production_text}: "
                                    f"'{terminal}' is added from "
                                    f"FOLLOW({lhs}) because the "
                                    f"remaining symbols can derive epsilon."
                                )

                                changed = True

    return follow_sets, explanations


# -------------------------------------------------
# COMPLETE FIRST AND FOLLOW ANALYSIS
# -------------------------------------------------

def calculate_first_follow(grammar_text):

    # Validate grammar first
    grammar_result = parse_grammar(grammar_text)

    if not grammar_result["valid"]:

        return {
            "valid": False,
            "errors": grammar_result["errors"],
            "start_symbol": None,
            "first": {},
            "follow": {},
            "first_explanations": {},
            "follow_explanations": {}
        }

    productions = grammar_result["productions"]

    non_terminals = set(
        grammar_result["non_terminals"]
    )

    start_symbol = grammar_result["start_symbol"]

    # Calculate FIRST
    first_sets, first_explanations = compute_first_sets(
        productions,
        non_terminals
    )

    # Calculate FOLLOW
    follow_sets, follow_explanations = compute_follow_sets(
        productions,
        non_terminals,
        first_sets,
        start_symbol
    )

    # Convert sets into sorted lists for easy display
    return {

        "valid": True,

        "start_symbol": start_symbol,

        "first": {
            nt: sorted(first_sets[nt])
            for nt in sorted(non_terminals)
        },

        "follow": {
            nt: sorted(follow_sets[nt])
            for nt in sorted(non_terminals)
        },

        "first_explanations": first_explanations,

        "follow_explanations": follow_explanations,

        "errors": []

    }


# -------------------------------------------------
# TEST THE FIRST AND FOLLOW MODULE
# -------------------------------------------------

if __name__ == "__main__":

    test_grammar = """
E->TE'
E'->+TE'|ε
T->FT'
T'->*FT'|ε
F->(E)|id
"""

    result = calculate_first_follow(
        test_grammar
    )

    print("\nFIRST AND FOLLOW SETS")
    print("=" * 45)

    if not result["valid"]:

        print("Invalid Grammar!")

        for error in result["errors"]:
            print(error)

    else:

        print(
            "Start Symbol:",
            result["start_symbol"]
        )

        print("\nFIRST SETS")
        print("-" * 45)

        for nt, symbols in result["first"].items():

            print(
                f"FIRST({nt}) = {format_set(symbols)}"
            )

        print("\nFOLLOW SETS")
        print("-" * 45)

        for nt, symbols in result["follow"].items():

            print(
                f"FOLLOW({nt}) = {format_set(symbols)}"
            )

        print("\nFIRST SET EXPLANATIONS")
        print("-" * 45)

        for nt, reasons in result["first_explanations"].items():

            print(f"\nFIRST({nt}):")

            for reason in reasons:
                print(" -", reason)

        print("\nFOLLOW SET EXPLANATIONS")
        print("-" * 45)

        for nt, reasons in result["follow_explanations"].items():

            print(f"\nFOLLOW({nt}):")

            for reason in reasons:
                print(" -", reason)
