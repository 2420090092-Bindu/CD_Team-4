
from .grammar import parse_grammar


# =========================================================
# FORMAT GRAMMAR
# =========================================================

def format_rhs(rhs):

    if not rhs:
        return "ε"

    return "".join(rhs)


def format_grammar(productions):

    lines = []

    for lhs, alternatives in productions.items():

        formatted_alternatives = [
            format_rhs(rhs)
            for rhs in alternatives
        ]

        lines.append(
            f"{lhs} -> " + " | ".join(formatted_alternatives)
        )

    return "\n".join(lines)


# =========================================================
# FIND COMMON PREFIX
# =========================================================

def common_prefix(first, second):

    prefix = []

    for a, b in zip(first, second):

        if a == b:
            prefix.append(a)

        else:
            break

    return prefix


# =========================================================
# GENERATE UNIQUE NON-TERMINAL
# =========================================================

def generate_new_non_terminal(lhs, non_terminals):

    candidate = lhs + "'"

    while candidate in non_terminals:
        candidate += "'"

    non_terminals.add(candidate)

    return candidate


# =========================================================
# FIND THE BEST PREFIX TO FACTOR
# =========================================================

def find_best_prefix(alternatives):

    best_prefix = []

    for i in range(len(alternatives)):

        for j in range(i + 1, len(alternatives)):

            prefix = common_prefix(
                alternatives[i],
                alternatives[j]
            )

            if len(prefix) > len(best_prefix):

                best_prefix = prefix

    if not best_prefix:
        return None

    return best_prefix


# =========================================================
# ELIMINATE LEFT FACTORING
# =========================================================

def eliminate_left_factoring(grammar_text):

    validation = parse_grammar(grammar_text)

    if not validation["valid"]:

        return {
            "valid": False,
            "has_left_factoring": False,
            "original_grammar": grammar_text,
            "transformed_grammar": "",
            "productions": {},
            "steps": [],
            "errors": validation["errors"]
        }

    productions = {
        lhs: [rhs[:] for rhs in alternatives]
        for lhs, alternatives in validation["productions"].items()
    }

    non_terminals = set(validation["non_terminals"])

    original_grammar = grammar_text

    steps = []

    # Process original and newly generated non-terminals
    pending = list(productions.keys())

    has_left_factoring = False

    while pending:

        lhs = pending.pop(0)

        alternatives = productions[lhs]

        while True:

            prefix = find_best_prefix(alternatives)

            # No common prefix remains
            if prefix is None:
                break

            # Find all alternatives starting with this prefix
            matching_indices = []

            for index, rhs in enumerate(alternatives):

                if rhs[:len(prefix)] == prefix:
                    matching_indices.append(index)

            if len(matching_indices) < 2:
                break

            has_left_factoring = True

            # Generate a new non-terminal
            new_nt = generate_new_non_terminal(
                lhs,
                non_terminals
            )

            # Create new alternatives for the helper NT
            new_alternatives = []

            for index in matching_indices:

                rhs = alternatives[index]

                suffix = rhs[len(prefix):]

                new_alternatives.append(suffix)

            # Replace the factored alternatives
            new_rhs = prefix + [new_nt]

            first_index = matching_indices[0]

            remaining_alternatives = []

            for index, rhs in enumerate(alternatives):

                if index == first_index:

                    remaining_alternatives.append(new_rhs)

                elif index not in matching_indices:

                    remaining_alternatives.append(rhs)

            # Update original non-terminal
            alternatives = remaining_alternatives

            productions[lhs] = alternatives

            # Add helper non-terminal
            productions[new_nt] = new_alternatives

            # Record transformation
            steps.append({

                "non_terminal": lhs,

                "common_prefix": format_rhs(prefix),

                "new_non_terminal": new_nt,

                "new_production": (
                    f"{lhs} -> {format_rhs(new_rhs)}"
                ),

                "helper_production": (
                    f"{new_nt} -> "
                    + " | ".join(
                        format_rhs(rhs)
                        for rhs in new_alternatives
                    )
                )

            })

            # Process the new helper NT also
            pending.append(new_nt)

    transformed_grammar = format_grammar(productions)

    return {

        "valid": True,

        "has_left_factoring": has_left_factoring,

        "original_grammar": original_grammar,

        "transformed_grammar": transformed_grammar,

        "productions": productions,

        "steps": steps,

        "errors": []

    }


# =========================================================
# DISPLAY RESULTS
# =========================================================

def display_left_factoring(result):

    print("\nLEFT FACTORING ANALYSIS")

    print("=" * 70)

    if not result["valid"]:

        print("Invalid grammar!")

        for error in result["errors"]:
            print(error)

        return

    print("\nORIGINAL GRAMMAR")

    print(result["original_grammar"])

    if not result["has_left_factoring"]:

        print("\nNo common prefixes found.")

        print("\nGrammar is already left factored.")

    else:

        print("\nLEFT FACTORING STEPS")

        print("-" * 70)

        for index, step in enumerate(result["steps"], 1):

            print(f"\nStep {index}")

            print(
                "Non-terminal:",
                step["non_terminal"]
            )

            print(
                "Common prefix:",
                step["common_prefix"]
            )

            print(
                "New production:",
                step["new_production"]
            )

            print(
                "Helper production:",
                step["helper_production"]
            )

        print("\nTRANSFORMED GRAMMAR")

        print(result["transformed_grammar"])


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    grammar = """
S->aAB|aAC
A->b
B->c
C->d
"""

    result = eliminate_left_factoring(grammar)

    display_left_factoring(result)
