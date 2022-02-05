# Lv7.1. 处理 `while`

本节新增/变更的语法规范如下:

```ebnf
Stmt ::= ...
       | ...
       | ...
       | ...
       | "while" "(" Exp ")" Stmt
       | ...;
```

## 一个例子

```c
int main() {
  int i = 0;
  while (i < 10) i = i + 1;
  return i;
}
```

## 词法/语法分析

本节新增了关键字 `while`, 你需要修改你的 lexer 来支持它们. 同时, 你需要针对 `while` 语句设计 AST, 并更新你的 parser 实现.

## 语义分析

无需新增内容. 记得对 `while` 的各部分 (条件和循环体) 进行语义分析即可.

## IR 生成

根据 `while` 的语义, 生成所需的基本块, 条件判断和分支/跳转指令即可. 相信在理解了 `if/else` 语句 IR 生成的原理之后, 这部分对你来说并不困难.

示例程序生成的 Koopa IR 为:

```koopa
fun @main(): i32 {
%entry:
  @i = alloc i32
  store 0, @i
  jump %while_entry

%while_entry:
  %0 = load @i
  %cond = lt %0, 10
  br %cond, %while_body, %end

%while_body:
  %1 = load @i
  %2 = add %1, 1
  store %2, @i
  jump %while_entry

%end:
  %3 = load @i
  ret %3
}
```

当然, 可能还存在其他生成 `while` 的方式.

## 目标代码生成

本节并未用到新的 Koopa IR 指令, 也不涉及 Koopa IR 中的新概念, 所以这部分没有需要改动的内容.
