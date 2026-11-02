%{
#include "parser.tab.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char *duplicate_text(const char *text)
{
    size_t length = strlen(text);
    char *copy = malloc(length + 1);

    if (copy != NULL)
    {
        strcpy(copy, text);
    }

    return copy;
}
%}

%%

"->"                    return ARROW;
"|"                     return OR;

[ \t\r]+                ;
\n                      return EOL;

[A-Z]                   {
                            yylval.str = duplicate_text(yytext);
                            return SYMBOL;
                        }

[a-z][a-z0-9_]*         {
                            yylval.str = duplicate_text(yytext);
                            return SYMBOL;
                        }

.                       {
                            yylval.str = duplicate_text(yytext);
                            return SYMBOL;
                        }

%%

int yywrap()
{
    return 1;
}