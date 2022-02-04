# Lv5. 语句块和作用域

本章中, 你将在上一章的基础上, 实现一个能够处理语句快和作用域的编译器.

你的编译器将可以处理如下的 SysY 程序:

```c
int main() {
  int a = 1, b = 2;
  {
    int a = 2;
    b = b + a;
  }
  return b;
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

* 单个 `Exp` 可以作为 `Stmt`. `Exp` 会被求值 (即存在副作用), 但所求的值会被丢弃.
* `Block` 表示语句块. 语句块会创建作用域, 语句块内声明的变量的生存期在该语句块内.
* 作用域是可以嵌套的, 因为语句块是可以嵌套的.
* 语句块内可以再次定义与语句块外同名的变量或常量 (通过 `Decl` 语句), 其作用域从定义处开始到该语句块尾结束, 它覆盖了语句块外的同名变量或常量.
* 对于同一个标识符, 在同一作用域中最多存在一次声明.
* `LVal` 必须是当前作用域内, 该 `Exp` 语句之前曾定义过的变量或常量. 赋值号左边的 `LVal` 必须是变量.
