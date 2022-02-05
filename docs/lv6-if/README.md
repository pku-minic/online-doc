# Lv6. `if` 语句

本章中, 你将在上一章的基础上, 实现一个能够处理 `if/else` 语句的编译器.

你的编译器将可以处理如下的 SysY 程序:

```c
int main() {
  int a = 1;
  if (a == 2 || a == 3) {
    return 0;
  } else {
    return a + 1;
  }
}
```

## 语法规范

```ebnf
CompUnit      ::= FuncDef;

Decl          ::= ConstDecl | VarDecl;
ConstDecl     ::= "const" BType ConstDef {"," ConstDef} ";";
BType         ::= "int";
ConstDef      ::= IDENT "=" ConstInitVal;
ConstInitVal  ::= ConstExp;
VarDecl       ::= BType VarDef {"," VarDef} ";";
VarDef        ::= IDENT | IDENT "=" InitVal;
InitVal       ::= Exp;

FuncDef       ::= FuncType IDENT "(" ")" Block;
FuncType      ::= "int";

Block         ::= "{" {BlockItem} "}";
BlockItem     ::= Decl | Stmt;
Stmt          ::= LVal "=" Exp ";"
                | [Exp] ";"
                | Block
                | "if" "(" Exp ")" Stmt ["else" Stmt]
                | "return" [Exp] ";";

Exp           ::= LOrExp;
LVal          ::= IDENT;
PrimaryExp    ::= "(" Exp ")" | LVal | Number;
Number        ::= INT_CONST;
UnaryExp      ::= PrimaryExp | UnaryOp UnaryExp;
UnaryOp       ::= "+" | "-" | "!";
MulExp        ::= UnaryExp | MulExp ("*" | "/" | "%") UnaryExp;
AddExp        ::= MulExp | AddExp ("+" | "-") MulExp;
RelExp        ::= AddExp | RelExp ("<" | ">" | "<=" | ">=") AddExp;
EqExp         ::= RelExp | EqExp ("==" | "!=") RelExp;
LAndExp       ::= EqExp | LAndExp "&&" EqExp;
LOrExp        ::= LAndExp | LOrExp "||" LAndExp;
ConstExp      ::= Exp;
```

## 语义规范

* 当 `Exp` 出现在表示条件判断的位置时 (例如出现在 `if` 的条件中), 表达式值为 0 时为假, 非 0 时为真.
* `Stmt` 中的 `if` 型语句遵循就近匹配的原则, 即 `else` 总和离它最近且没有匹配到 `else` 的 `if` 进行匹配. 例如:

```c
if (x) if (y) ...; else ...;
// 等价于
if (x) {
  if (y) {
    ...;
  } else {
    ...;
  }
}
```
