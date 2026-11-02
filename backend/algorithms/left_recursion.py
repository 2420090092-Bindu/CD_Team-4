
try:
    from .grammar import parse_grammar
except ImportError:
    from grammar import parse_grammar


# -------------------------------------------------
# FORMAT A PRODUCTION
# -------------------------------------------------

def format_production(rhs):

    if not rhs:
        return "ε"

    return "".join(rhs)


# -------------------------------------------------
# FORMAT COMPLETE GRAMMAR
# -------------------------------------------------

def format_grammar(productions):

    lines = []

    for lhs, alternatives in productions.items():

        formatted_alternatives = [
            format_production(rhs)
            for rhs in alternatives
        ]

        if formatted_alternatives:
            rhs_text = " | ".join(formatted_alternatives)
            lines.append(f"{lhs} -> {rhs_text}")

    return "\n".join(lines)


# -------------------------------------------------
# GENERATE A UNIQUE NEW NON-TERMINAL
# -------------------------------------------------

def generate_new_symbol(symbol, existing_symbols):

    new_symbol = symbol + "'"

    while new_symbol in existing_symbols:
        new_symbol += "'"

    existing_symbols.add(new_symbol)

    return new_symbol


# -------------------------------------------------
# ELIMINATE IMMEDIATE LEFT RECURSION
# -------------------------------------------------

def eliminate_immediate_left_recursion(grammar_text):

    # Parse and validate the original grammar
    result = parse_grammar(grammar_text)

    if not result["valid"]:

        return {
            "valid": False,
            "has_left_recursion": False,
            "original_grammar": grammar_text,
            "transformed_grammar": None,
            "steps": [],
            "errors": result["errors"]
        }

    productions = result["productions"]

    existing_symbols = set(
        result["non_terminals"]
    )

    transformed = {}
    steps = []
    has_left_recursion = False

    # ---------------------------------------------
    # PROCESS EACH NON-TERMINAL
    # ---------------------------------------------

    for lhs, alternatives in productions.items():

        alpha = []
        beta = []

        self_loop_found = False

        # -----------------------------------------
        # SEPARATE ALPHA AND BETA
        # -----------------------------------------

        for rhs in alternatives:

            # Immediate left recursion:
            # A -> A alpha

            if rhs and rhs[0] == lhs:

                suffix = rhs[1:]

                if suffix:
                    alpha.append(suffix)
                else:
                    self_loop_found = True

            else:

                # Non-left-recursive production:
                # A -> beta

                beta.append(rhs)

        # -----------------------------------------
        # NO LEFT RECURSION
        # -----------------------------------------

        if not alpha and not self_loop_found:

            transformed[lhs] = alternatives

            steps.append(
                f"No immediate left recursion found for {lhs}."
            )

            continue

        has_left_recursion = True

        # -----------------------------------------
        # REMOVE REDUNDANT SELF LOOP
        # -----------------------------------------

        if not alpha and self_loop_found:

            if not beta:

                return {
                    "valid": False,
                    "has_left_recursion": True,
                    "original_grammar": grammar_text,
                    "transformed_grammar": None,
                    "steps": steps,
                    "errors": [
                        f"{lhs} has only the production "
                        f"{lhs} -> {lhs} and has no "
                        "non-left-recursive alternative."
                    ]
                }

            transformed[lhs] = beta

            steps.append(
                f"Removed redundant self-loop "
                f"{lhs} -> {lhs}."
            )

            continue

        # -----------------------------------------
        # CHECK FOR BETA PRODUCTIONS
        # -----------------------------------------

        if not beta:

            return {
                "valid": False,
                "has_left_recursion": True,
                "original_grammar": grammar_text,
                "transformed_grammar": None,
                "steps": steps,
                "errors": [
                    f"Cannot eliminate left recursion "
                    f"for {lhs}: no non-left-recursive "
                    "alternative (beta) exists."
                ]
            }

        # -----------------------------------------
        # CREATE NEW NON-TERMINAL
        # -----------------------------------------

        new_symbol = generate_new_symbol(
            lhs,
            existing_symbols
        )

        # -----------------------------------------
        # APPLY LEFT RECURSION ELIMINATION
        # -----------------------------------------

        # A -> beta A'

        transformed[lhs] = [
            rhs + [new_symbol]
            for rhs in beta
        ]

        # A' -> alpha A' | epsilon

        transformed[new_symbol] = [
            rhs + [new_symbol]
            for rhs in alpha
        ]

        transformed[new_symbol].append([])

        # -----------------------------------------
        # DISPLAY TRANSFORMATION STEPS
        # -----------------------------------------

        alpha_text = [
            format_production(rhs)
            for rhs in alpha
        ]

        beta_text = [
            format_production(rhs)
            for rhs in beta
        ]

        steps.append(
            f"\nImmediate left recursion found in {lhs}."
        )

        steps.append(
            f"Alpha productions: {alpha_text}"
        )

        steps.append(
            f"Beta productions: {beta_text}"
        )

        steps.append(
            f"Create a new non-terminal: {new_symbol}"
        )

        steps.append(
            f"Replace {lhs} productions with beta followed by {new_symbol}."
        )

        steps.append(
            f"New productions: "
            f"{lhs} -> "
            + " | ".join(
                format_production(rhs)
                for rhs in transformed[lhs]
            )
        )

        steps.append(
            f"{new_symbol} -> "
            + " | ".join(
                format_production(rhs)
                for rhs in transformed[new_symbol]
            )
        )

    # ---------------------------------------------
    # FINAL RESULT
    # ---------------------------------------------

    return {

        "valid": True,

        "has_left_recursion": has_left_recursion,

        "original_grammar": format_grammar(
            productions
        ),

        "transformed_grammar": format_grammar(
            transformed
        ),

        "productions": transformed,

        "steps": steps,

        "errors": []

    }


# -------------------------------------------------
# TEST THE MODULE
# -------------------------------------------------

if __name__ == "__main__":

    test_grammar = """
E->E+T|T
T->T*F|F
F->(E)|id
"""

    result = eliminate_immediate_left_recursion(
        test_grammar
    )

    print("\nLEFT RECURSION ELIMINATION")
    print("--------------------------------")

    if result["valid"]:

        print("Grammar Valid: Yes")

        print(
            "\nOriginal Grammar:\n"
        )

        print(result["original_grammar"])

        print(
            "\nTransformation Steps:"
        )

        for step in result["steps"]:
            print(step)

        print(
            "\nFinal Grammar:\n"
        )

        print(result["transformed_grammar"])

    else:

        print("Grammar Valid: No")

        for error in result["errors"]:
            print(error)
