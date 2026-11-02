%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

int yylex(void);
int yyerror(const char *s);

#define MAX_PRODUCTIONS 100
#define MAX_RHS_SYMBOLS 50
#define MAX_SYMBOL_LEN 64
#define MAX_TREE_DEPTH 100

/* ---------------- Production ---------------- */

typedef struct {
    char lhs[MAX_SYMBOL_LEN];
    char rhs[MAX_RHS_SYMBOLS][MAX_SYMBOL_LEN];
    int rhs_count;
} Production;

Production productions[MAX_PRODUCTIONS];
int production_count = 0;

char current_lhs[MAX_SYMBOL_LEN];
char current_rhs[MAX_RHS_SYMBOLS][MAX_SYMBOL_LEN];
int current_rhs_count = 0;

/* ---------------- Parse Tree Node ---------------- */

typedef struct Node {
    char symbol[MAX_SYMBOL_LEN];
    struct Node *children[MAX_RHS_SYMBOLS];
    int child_count;
} Node;


/* ==================================================
   PRODUCTION FUNCTIONS
   ================================================== */

void start_rule(char *lhs)
{
    strncpy(
        current_lhs,
        lhs,
        MAX_SYMBOL_LEN - 1
    );

    current_lhs[MAX_SYMBOL_LEN - 1] = '\0';

    current_rhs_count = 0;
}


void add_rhs_symbol(char *symbol)
{
    if (current_rhs_count >= MAX_RHS_SYMBOLS)
        return;

    strncpy(
        current_rhs[current_rhs_count],
        symbol,
        MAX_SYMBOL_LEN - 1
    );

    current_rhs[current_rhs_count][MAX_SYMBOL_LEN - 1] = '\0';

    current_rhs_count++;
}


void reset_rhs()
{
    current_rhs_count = 0;
}


void save_production()
{
    if (production_count >= MAX_PRODUCTIONS)
        return;

    strncpy(
        productions[production_count].lhs,
        current_lhs,
        MAX_SYMBOL_LEN - 1
    );

    productions[production_count].lhs[MAX_SYMBOL_LEN - 1] = '\0';

    productions[production_count].rhs_count =
        current_rhs_count;

    for (int i = 0; i < current_rhs_count; i++)
    {
        strncpy(
            productions[production_count].rhs[i],
            current_rhs[i],
            MAX_SYMBOL_LEN - 1
        );

        productions[production_count].rhs[i]
                              [MAX_SYMBOL_LEN - 1] = '\0';
    }

    production_count++;

    reset_rhs();
}


/* ==================================================
   PARSE TREE FUNCTIONS
   ================================================== */

Node *create_node(const char *symbol)
{
    Node *node = malloc(sizeof(Node));

    if (node == NULL)
    {
        printf("Memory allocation failed.\n");
        exit(1);
    }

    strncpy(
        node->symbol,
        symbol,
        MAX_SYMBOL_LEN - 1
    );

    node->symbol[MAX_SYMBOL_LEN - 1] = '\0';

    node->child_count = 0;

    for (int i = 0; i < MAX_RHS_SYMBOLS; i++)
    {
        node->children[i] = NULL;
    }

    return node;
}


int is_non_terminal(const char *symbol)
{
    return (
        strlen(symbol) == 1 &&
        isupper((unsigned char)symbol[0])
    );
}


int find_production(const char *symbol)
{
    for (int i = 0; i < production_count; i++)
    {
        if (strcmp(
                productions[i].lhs,
                symbol
            ) == 0)
        {
            return i;
        }
    }

    return -1;
}


/* Check whether this non-terminal is already
   being expanded on the current path */

int is_already_in_path(
    const char *symbol,
    char path[][MAX_SYMBOL_LEN],
    int path_count
)
{
    for (int i = 0; i < path_count; i++)
    {
        if (strcmp(path[i], symbol) == 0)
        {
            return 1;
        }
    }

    return 0;
}


/*
   Build one representative parse tree.

   The path array prevents infinite recursion
   for grammars such as:

       E->E+E
       E->E*E
       E->id
*/

Node *build_tree(
    const char *symbol,
    char path[][MAX_SYMBOL_LEN],
    int path_count
)
{
    Node *node = create_node(symbol);

    /* Terminal: no children */
    if (!is_non_terminal(symbol))
    {
        return node;
    }

    /* Prevent recursive loops */
    if (
        path_count >= MAX_TREE_DEPTH ||
        is_already_in_path(
            symbol,
            path,
            path_count
        )
    )
    {
        return node;
    }

    int production_index =
        find_production(symbol);

    if (production_index == -1)
    {
        return node;
    }

    /* Add current symbol to path */
    strncpy(
        path[path_count],
        symbol,
        MAX_SYMBOL_LEN - 1
    );

    path[path_count][MAX_SYMBOL_LEN - 1] = '\0';

    Production *production =
        &productions[production_index];

    for (int i = 0;
         i < production->rhs_count;
         i++)
    {
        if (node->child_count >= MAX_RHS_SYMBOLS)
            break;

        node->children[node->child_count] =
            build_tree(
                production->rhs[i],
                path,
                path_count + 1
            );

        node->child_count++;
    }

    return node;
}


void print_tree(Node *node, int level)
{
    for (int i = 0; i < level; i++)
    {
        printf("    ");
    }

    printf("%s\n", node->symbol);

    for (int i = 0;
         i < node->child_count;
         i++)
    {
        print_tree(
            node->children[i],
            level + 1
        );
    }
}


void free_tree(Node *node)
{
    if (node == NULL)
        return;

    for (int i = 0;
         i < node->child_count;
         i++)
    {
        free_tree(node->children[i]);
    }

    free(node);
}


/* ==================================================
   BISON GRAMMAR
   ================================================== */

%}

%union {
    char *str;
}

%token <str> SYMBOL
%token ARROW
%token OR
%token EOL

%%

input:
    rules
    ;

rules:
      /* empty */
    | rules rule
    ;

rule:
    SYMBOL
    {
        start_rule($1);
        free($1);
    }
    ARROW alternatives EOL
    ;

alternatives:
      rhs
    {
        save_production();
    }

    | alternatives OR rhs
    {
        save_production();
    }
    ;

rhs:
      SYMBOL
    {
        add_rhs_symbol($1);
        free($1);
    }

    | rhs SYMBOL
    {
        add_rhs_symbol($2);
        free($2);
    }
    ;

%%


int yyerror(const char *s)
{
    fprintf(
        stderr,
        "Parser error: %s\n",
        s
    );

    return 0;
}


int main()
{
    if (yyparse() == 0)
    {
        printf(
            "CFG parsed successfully!\n"
        );

        printf(
            "Production rules detected: %d\n\n",
            production_count
        );

        printf("Parse Tree:\n");

        if (production_count > 0)
        {
            char path[
                MAX_TREE_DEPTH
            ][MAX_SYMBOL_LEN];

            Node *root =
                build_tree(
                    productions[0].lhs,
                    path,
                    0
                );

            print_tree(root, 0);

            free_tree(root);
        }
    }

    return 0;
}