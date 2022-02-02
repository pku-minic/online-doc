# Lv3. 表达式

本章中, 你将在上一章的基础上, 实现一个能够处理表达式 (一元/二元) 的编译器.

你的编译器将可以处理如下的 SysY 程序:

```c
int main() {
  return 1 + 2 * -3;
}
```

## 语法规范

```ebnf
CompUnit    ::= FuncDef;

FuncDef     ::= FuncType IDENT "(" ")" Block;
FuncType    ::= "int";

Block       ::= "{" Stmt "}";
Stmt        ::= "return" Expr ";";

Exp         ::= LOrExp;
PrimaryExp  ::= "(" Exp ")" | Number;
Number      ::= INT_CONST;
UnaryExp    ::= PrimaryExp | UnaryOp UnaryExp;
UnaryOp     ::= "+" | "-" | "!";
MulExp      ::= UnaryExp | MulExp ("*" | "/" | "%") UnaryExp;
AddExp      ::= MulExp | AddExp ("+" | "-") MulExp;
RelExp      ::= AddExp | RelExp ("<" | ">" | "<=" | ">=") AddExp;
EqExp       ::= RelExp | EqExp ("==" | "!=") RelExp;
LAndExp     ::= EqExp | LAndExp "&&" EqExp;
LOrExp      ::= LAndExp | LOrExp "||" LAndExp;
```

## 语义规范

* 所有表达式的类型均为 `int` 型 (计算结果为整数).
* 对于 `LOrExp`, 当其左右操作数有任意一个非 0 时, 表达式的值为 1, 否则为 0; 对于 `LAndExp`, 当其左右操作数有任意一个为 0 时, 表达式的值为 0, 否则为 1. 上述两种表达式暂时不需要进行短路求值.
* SysY 中算符的优先级与结合性与 C 语言一致, SysY 的语法规范中已体现了优先级与结合性的定义.
* SysY 中的整数是 32 位无符号整数. 与 C 语言一致, 整数运算溢出在 SysY 中属于未定义行为 ([undefined behavior](https://en.wikipedia.org/wiki/Undefined_behavior)).
