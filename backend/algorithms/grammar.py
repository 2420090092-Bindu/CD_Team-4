
import re


# Supported epsilon symbols
EPSILON_SYMBOLS = {"ε", "ϵ", "#", "epsilon"}

NON_TERMINAL_PATTERN = re.compile(
    r"[A-Z][A-Za-z0-9_']*"
)


# -------------------------------------------------
# TOKENIZE RIGHT-HAND SIDE
# -------------------------------------------------

def tokenize_rhs(rhs, non_terminals):

    rhs = rhs.strip()

    # Epsilon alone is a valid empty production
    if rhs.casefold() in EPSILON_SYMBOLS:
        return []

    # Epsilon cannot be combined with other symbols
    if (
        "ε" in rhs
        or "ϵ" in rhs
        or "#" in rhs
        or re.search(r"epsilon", rhs, re.IGNORECASE)
    ):
        raise ValueError(
            "Epsilon must appear alone in a production."
        )

    tokens = []
    position = 0

    # Match longer non-terminals first
    sorted_non_terminals = sorted(
        non_terminals,
        key=len,
        reverse=True
    )

    while position < len(rhs):

        char = rhs[position]

        # Ignore whitespace
        if char.isspace():
            position += 1
            continue

        matched = False

        # Identify declared non-terminals
        for nt in sorted_non_terminals:

            if rhs.startswith(nt, position):

                tokens.append(nt)
                position += len(nt)
                matched = True
                break

        if matched:
            continue

        # Identify uppercase non-terminals
        if char.isupper():

            match = re.match(
                r"[A-Z][A-Za-z0-9_']*",
                rhs[position:]
            )

            if match:

                symbol = match.group()
                tokens.append(symbol)
                position += len(symbol)
                continue

        # Identify lowercase terminals
        if char.islower():

            match = re.match(
                r"[a-z][a-z0-9_]*",
                rhs[position:]
            )

            if match:

                symbol = match.group()
                tokens.append(symbol)
                position += len(symbol)
                continue

        # Identify operators and special symbols
        tokens.append(char)
        position += 1

    return tokens


# -------------------------------------------------
# PARSE AND VALIDATE CFG
# -------------------------------------------------

def parse_grammar(grammar_text):

    errors = []
    warnings = []

    productions = {}
    non_terminals = set()

    start_symbol = None
    raw_rules = []

    # Check empty input
    if not grammar_text or not grammar_text.strip():

        return {
            "valid": False,
            "start_symbol": None,
            "productions": {},
            "non_terminals": [],
            "terminals": [],
            "errors": ["Grammar cannot be empty."],
            "warnings": []
        }

    # Normalize line endings
    grammar_text = grammar_text.replace(
        "\r\n", "\n"
    ).replace(
        "\r", "\n"
    )

    # Support Unicode production arrow
    grammar_text = grammar_text.replace(
        "→", "->"
    )

    # ---------------------------------------------
    # FIRST PASS: IDENTIFY NON-TERMINALS
    # ---------------------------------------------

    for line_number, line in enumerate(
        grammar_text.splitlines(),
        start=1
    ):

        line = line.strip()

        if not line:
            continue

        if "->" not in line:

            errors.append(
                f"Line {line_number}: Missing production arrow (->)."
            )

            continue

        lhs, rhs = line.split("->", 1)

        lhs = lhs.strip()
        rhs = rhs.strip()

        # Validate LHS
        if not NON_TERMINAL_PATTERN.fullmatch(lhs):

            errors.append(
                f"Line {line_number}: Invalid non-terminal '{lhs}'."
            )

            continue

        if not rhs:

            errors.append(
                f"Line {line_number}: Production for '{lhs}' is empty. Use epsilon explicitly."
            )

            continue

        if "->" in rhs:

            errors.append(
                f"Line {line_number}: Unexpected production arrow in RHS."
            )

            continue

        if start_symbol is None:
            start_symbol = lhs

        non_terminals.add(lhs)

        raw_rules.append(
            (lhs, rhs, line_number)
        )

    # ---------------------------------------------
    # SECOND PASS: PROCESS PRODUCTION RULES
    # ---------------------------------------------

    for lhs, rhs, line_number in raw_rules:

        alternatives = rhs.split("|")

        productions.setdefault(lhs, [])

        for alternative in alternatives:

            alternative = alternative.strip()

            if not alternative:

                errors.append(
                    f"Line {line_number}: Empty alternative in '{lhs}'. Use epsilon explicitly."
                )

                continue

            try:

                symbols = tokenize_rhs(
                    alternative,
                    non_terminals
                )

                # Check undefined non-terminals
                for symbol in symbols:

                    if (
                        NON_TERMINAL_PATTERN.fullmatch(symbol)
                        and symbol not in non_terminals
                    ):

                        errors.append(
                            f"Line {line_number}: Undefined non-terminal '{symbol}'."
                        )

                # Check duplicate productions
                if symbols in productions[lhs]:

                    warnings.append(
                        f"Line {line_number}: Duplicate production found for '{lhs}'."
                    )

                else:

                    productions[lhs].append(
                        symbols
                    )

            except ValueError as e:

                errors.append(
                    f"Line {line_number}: {str(e)}"
                )

    # ---------------------------------------------
    # IDENTIFY TERMINALS
    # ---------------------------------------------

    terminals = set()

    for lhs, alternatives in productions.items():

        for rhs in alternatives:

            for symbol in rhs:

                if symbol not in non_terminals:
                    terminals.add(symbol)

    # ---------------------------------------------
    # RETURN RESULTS
    # ---------------------------------------------

    return {

        "valid": (
            len(errors) == 0
            and start_symbol is not None
        ),

        "start_symbol": start_symbol,

        "productions": productions,

        "non_terminals": sorted(
            non_terminals
        ),

        "terminals": sorted(
            terminals
        ),

        "errors": errors,

        "warnings": warnings

    }


# -------------------------------------------------
# TEST THE GRAMMAR MODULE
# -------------------------------------------------

if __name__ == "__main__":

    test_grammar = """
S->AB|a
A->a|ε
B->b
"""

    result = parse_grammar(test_grammar)

    print("\nCFG GRAMMAR ANALYSIS")
    print("----------------------------")

    print("Valid:", result["valid"])

    print("Start Symbol:", result["start_symbol"])

    print("Non-terminals:", result["non_terminals"])

    print("Terminals:", result["terminals"])

    print("\nProduction Rules:")

    for lhs, alternatives in result["productions"].items():

        for rhs in alternatives:

            production = (
                " ".join(rhs) if rhs else "ε"
            )

            print(f"{lhs} -> {production}")

    print("\nErrors:", result["errors"])

    print("Warnings:", result["warnings"])
