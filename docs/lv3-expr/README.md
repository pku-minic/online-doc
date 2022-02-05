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
Stmt        ::= "return" Exp ";";

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
* 对于 `LOrExp`, 当其左右操作数有任意一个非 0 时, 表达式的值为 1, 否则为 0; 对于 `LAndExp`, 当其左右操作数有任意一个为 0 时, 表达式的值为 0, 否则为 1. 上述两种表达式**暂时不需要进行短路求值**.
* SysY 中算符的功能, 优先级与结合性均与 C 语言一致, SysY 的语法规范中已体现了优先级与结合性的定义.
* SysY 中的整数是 32 位无符号整数. 与 C 语言一致, 无符号整数运算溢出在 SysY 中属于未定义行为 ([undefined behavior](https://en.wikipedia.org/wiki/Undefined_behavior)).

?> 未定义行为缩写为 UB, 如果你的代码里出现了 UB, 那么程序执行时的行为就是不可定义的 (发生什么事都有可能, ~~比如你系统盘被程序格了~~). 除了无符号整数溢出, C/C++ 中有很多行为都属于 UB, 比如数组访问越界. [这里](https://gist.github.com/Earnestly/7c903f481ff9d29a3dd1)有一份 C99 的 UB 列表.
<br><br>
编译器可以利用 UB 进行一些非常激进的优化. 比如, 编译器可以假定程序永远都不会发生 UB, 然后标记 UB 出现的位置是不可达的, 最后删掉不可达代码.
<br><br>
经常有所谓的 “老一辈人士” 给你一些 “忠告”: 编译 C/C++ 的时候优化不能开到 `-O3`, 编译出来的程序会出问题, 因为编译器有 bug——这种说法基本就是扯淡, 因为虽然编译器确实会出现 bug, 但你遇到 bug 的概率总体来说还是很低的. 程序出问题的原因几乎都是代码写出了 UB, 然后被编译器给优化飞了. 解决这个问题的最好办法是, 呃……不要写出 UB.
