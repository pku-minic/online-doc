# Lv4.1. 常量

本节涉及的语法规范如下:

```ebnf
CompUnit      ::= FuncDef;

(* 新增部分 *)
Decl          ::= ConstDecl;
ConstDecl     ::= "const" BType ConstDef {"," ConstDef} ";";
BType         ::= "int";
ConstDef      ::= IDENT "=" ConstInitVal;
ConstInitVal  ::= ConstExp;
(* 新增部分结束 *)

FuncDef       ::= FuncType IDENT "(" ")" Block;
FuncType      ::= "int";

(* 变更部分 *)
Block         ::= "{" {BlockItem} "}";
BlockItem     ::= Decl | Stmt;
(* 变更部分结束 *)
Stmt          ::= "return" Exp ";";

Exp           ::= LOrExp;
(* 变更部分 *)
LVal          ::= IDENT;
PrimaryExp    ::= "(" Exp ")" | LVal | Number;
(* 变更部分结束 *)
Number        ::= INT_CONST;
UnaryExp      ::= PrimaryExp | UnaryOp UnaryExp;
UnaryOp       ::= "+" | "-" | "!";
MulExp        ::= UnaryExp | MulExp ("*" | "/" | "%") UnaryExp;
AddExp        ::= MulExp | AddExp ("+" | "-") MulExp;
RelExp        ::= AddExp | RelExp ("<" | ">" | "<=" | ">=") AddExp;
EqExp         ::= RelExp | EqExp ("==" | "!=") RelExp;
LAndExp       ::= EqExp | LAndExp "&&" EqExp;
LOrExp        ::= LAndExp | LOrExp "||" LAndExp;
(* 新增部分 *)
ConstExp      ::= Exp;
(* 新增部分结束 *)
```

## 一个例子

```c
int main() {
  const int x = 1 + 1;
  return x;
}
```

## 词法/语法分析

本节增加了一些新的关键字, 你需要修改 lexer 来支持它们. 同样, 你需要根据新增的语法规则, 来设计新的 AST, 以及更新你的 parser 实现.

本节的 EBNF 中出现了一种新的表示: `{ ... }`, 这代表花括号内包含的项可被重复 0 次或多次. 在 AST 中, 你可以使用 `std::vector`/`Vec` 来表示这种结构.

## 语义分析

本章的语义规范较前几章来说复杂了许多, 你需要在编译器中引入一些额外的结构, 以便进行必要的语义分析. 这种结构叫做**符号表**.

符号表可以记录作用域内所有被定义过的符号的信息. 在本节中, 符号表负责记录 `main` 函数中, 常量符号和其值之间的关系. 具体来说, 符号表需要支持如下操作:

* **插入符号定义:** 向符号表中添加一个常量符号, 同时记录这个符号的常量值, 也就是一个 32 位整数.
* **确认符号定义是否存在:** 给定一个符号, 查询符号表中是否存在这个符号的定义.
* **查询符号定义:** 给定一个符号表中已经存在的符号, 返回这个符号对应的常量值.

你可以选用合适的数据结构来实现符号表.

在遇到常量声明语句时, 你应该遍历 AST, 直接算出语句右侧的 `ConstExp` 的值, 得到一个 32 位整数, 然后把这个常量定义插入到符号表中.

在遇到 `LVal` 时, 你应该从符号表中查询这个符号的值, 然后用查到的结果作为常量求值/IR 生成的结果. 如果没查到, 说明 SysY 程序出现了语义错误, 也就是程序里使用了未定义的常量.

你可能需要给你的 AST 扩展一些必要的方法, 来实现编译期常量求值.

## IR 生成

所有的常量定义均已在编译期被求值, 所以:

* `Exp` 里, 所有出现 `LVal` 的地方均可直接替换为整数常量.
* 因上一条, 常量声明本身不需要生成任何 IR.

综上所述, 本节的 IR 生成部分不需要做任何修改.

示例程序生成的 Koopa IR 为:

```koopa
fun @main(): i32 {
%entry:
  ret 2
}
```

## 目标代码生成

由于 IR 生成部分未作修改, 目标代码生成部分也无需变更.

示例程序生成的 RISC-V 汇编为:

```
  .text
  .globl main
main:
  li a0, 2
  ret
```
