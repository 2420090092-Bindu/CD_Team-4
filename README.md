# 🌳 Interactive Context-Free Grammar Analyzer

### Parse Tree Generation, Ambiguity Detection, and Grammar Transformation

## 📌 Project Overview

The **Interactive Context-Free Grammar Analyzer** is a tool designed to simplify the understanding of compiler design concepts through visual representation and interactive grammar analysis.

The system allows users to input a Context-Free Grammar (CFG) and a test string to generate corresponding parse trees, detect grammar ambiguity, and understand how different derivations produce different parse structures.

It also identifies the reasons behind ambiguity and suggests grammar transformations such as left factoring, left-recursion elimination, and precedence/associativity rules to resolve ambiguity.

The main objective is to transform abstract compiler design concepts into an interactive and visual learning experience.

## 🎯 Problem Statement

Traditional grammar analysis tools generally generate only a single parse tree and provide limited support for understanding ambiguous grammars.

Students often find it difficult to identify why a grammar is ambiguous, understand different derivations, and perform grammar transformations.

This project addresses these limitations by providing an interactive platform for parse tree generation, ambiguity detection, explanation, and grammar transformation.

## ✨ Key Features

- **CFG Input and Validation:** Accepts user-defined Context-Free Grammars and validates their structure.
- **Parse Tree Generation:** Generates parse trees for the given input string.
- **Ambiguity Detection:** Identifies whether an input string has multiple valid parse trees.
- **Multiple Derivations:** Displays different possible derivations, including leftmost and rightmost derivations.
- **Ambiguity Explanation:** Highlights where different derivations produce different parse structures.
- **Grammar Transformation:** Suggests techniques to resolve ambiguity.
- **Before-and-After Comparison:** Compares the original and transformed grammars.
- **Ambiguity Verification:** Re-parses the input using the revised grammar to verify whether ambiguity has been resolved.

## ⚙️ How It Works

1. The user enters a Context-Free Grammar.
2. The user provides an input string.
3. The system validates the grammar.
4. The analyzer generates the corresponding parse tree or trees.
5. If multiple valid parse trees exist, the grammar is flagged as ambiguous.
6. The system explains the reason for ambiguity.
7. Suitable grammar transformation techniques are suggested.
8. The revised grammar is tested again to verify ambiguity resolution.

## 🧪 Example: Ambiguous Grammar

**Original Grammar:**

```text
E → E + E | E * E | id
```

**Input String:**

```text
id + id * id
```

The input string can produce two different parse structures:

**Parse Tree 1:**

```text
(id + id) * id
```

**Parse Tree 2:**

```text
id + (id * id)
```

Since the same input string produces multiple valid parse trees, the grammar is identified as ambiguous.

## 🔧 Ambiguity Resolution

The ambiguity occurs because the original grammar does not define operator precedence between `+` and `*`.

The system suggests assigning higher precedence to multiplication.

**Revised Grammar:**

```text
E → E + T | T
T → T * F | F
F → id
```

Here:
- `*` has higher precedence than `+`.
- The grammar separates expression, term, and factor levels.
- The input string is parsed again using the revised grammar.
- The resulting parse tree represents the intended operator precedence.

## 🏗️ System Architecture

The project follows this overall workflow:

```text
      User Input
          |
          v
   CFG + Test String
          |
          v
    Grammar Validation
          |
          v
   Parse Tree Generation
          |
          v
   Ambiguity Detection
          |
     +----+----+
     |         |
  Ambiguous  Unambiguous
     |
     v
 Ambiguity Explanation
     |
     v
 Transformation Suggestions
     |
     v
   Revised Grammar
     |
     v
  Re-Parsing & Verification
     |
     v
   Final Parse Tree
```

## 📚 Core Concepts Used

- Context-Free Grammar (CFG)
- Compiler Design
- Parse Tree Construction
- Leftmost Derivation
- Rightmost Derivation
- Grammar Ambiguity
- Left Factoring
- Left-Recursion Elimination
- Operator Precedence
- Associativity
- Abstract Syntax Trees (AST)

## 🚀 Future Enhancements

- LL(1) parsing table construction.
- LR parsing table generation.
- Interactive grammar editing and visualization.
- Code generation from parse trees.
- Support for additional grammar transformation techniques.
- Enhanced visualization of parsing steps.

## 👩‍💻 Team Members

| Name | Roll Number |
|---|---|
| Bindu Potukuchi | 2420090092 |
| Sarvani Topella | 2420030367 |
| Tanvi Bandaru | 2420030507 |
| Varshitha Ravuri | 2420030536 |

**Project Guide:** Dr. Krishna Kishore

**Course:** Compiler Design  
**Academic Year:** 2026–2027  
**Department:** Computer Science and Engineering

## 🎓 Objective

To make Context-Free Grammar analysis easier by combining parse tree visualization, ambiguity detection, and grammar transformation into a single interactive learning platform.
