# Lv4. 常量和变量

本章中, 你将在上一章的基础上, 实现一个能够处理常量/变量定义和赋值语句的编译器.

你的编译器将可以处理如下的 SysY 程序:

```c
int main() {
  const int x = 233 * 4;
  int y = 10;
  y = y + x / 2;
  return y;
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
                | "return" Exp ";";

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

* `ConstDef` 用于定义常量. `ConstDef` 中的 `IDENT` 为常量的标识符, 在 `=` 之后是初始值.
* `VarDef` 用于定义变量. 当不含有 `=` 和初始值时, 其运行时实际初值未定义.
* 当 `VarDef` 含有 `=` 和初始值时, `=` 右边的 `InitVal` 和 `ConstInitVal` 的结构要求相同, 唯一的不同是 `ConstInitVal` 中的表达式是 `ConstExp` 常量表达式, 而 `InitVal` 中的表达式可以是当前上下文合法的任何 `Exp`.
* `ConstExp` 内使用的 `IDENT` 必须是常量, 所有 `ConstExp` 必须在编译时被计算出来.
* `Block` 内不允许声明重名的变量或常量.
* `Block` 内定义的变量/常量在定义处到该语句块尾的范围内有效.
* 变量/常量的名字可以是 `main`.
* `Exp` 内出现的 `LVal` 必须是该 `Exp` 语句之前曾定义过的变量或常量.
* 对于赋值语句, 赋值号左边的 `LVal` 必须是变量, 不能是常量.
* 和 C 语言不同, SysY 中的赋值语句不会返回任何结果.
* `main` 函数中必须至少存在一条 `return` 语句. 不存在 `return` 时, `main` 函数的返回值是未定义的.
