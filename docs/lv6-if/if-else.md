# Lv6.1. 处理 `if/else`

本节新增/变更的语法规范如下:

```ebnf
Stmt ::= ...
       | ...
       | ...
       | "if" "(" Exp ")" Stmt ["else" Stmt]
       | ...;
```

## 一个例子

```c
int main() {
  int a = 2;
  if (a) {
    a = a + 1
  } else a = 0;  // 在实际写 C/C++ 程序的时候别这样, 建议 if 的分支全部带大括号
  return a;
}
```

## 词法/语法分析

本节新增了关键字 `if` 和 `else`, 你需要修改你的 lexer 来支持它们. 同时, 你需要针对 `if/else` 语句设计 AST, 并更新你的 parser 实现.

如果你完全按照本文档之前的内容, 例如选用了 C/C++ + Flex/Bison, 或 Rust + lalrpop 来实现你的编译器, 那么你在为你的 parser 添加 `if/else` 的语法时, 应该会遇到一些语法二义性导致的问题. 例如, Bison 会提示你发生了移进/规约冲突, lalrpop 会检测到二义性文法并拒绝生成 parser.

这个问题产生的原因是, 在 SysY (C 语言) 中, `if/else` 语句的 `else` 部分可有可无, 一旦出现了若干个 `if` 和一个 `else` 的组合, 在符合 EBNF 语法定义的前提下, 我们可以找到不止一种语法的推导 (或规约) 方法. 例如对于如下 SysY 程序:

```c
if (a) if (b) x; else y;
```

我们可以这样推导:

```
Stmt
-> "if" "(" Exp ")" Stmt
-> "if" "(" "a" ")" "if" "(" Exp ")" Stmt "else" Stmt
-> "if" "(" "a" ")" "if" "(" "b" ")" "x" ";" "else" "y" ";"
```

也可以这样:

```
Stmt
-> "if" "(" Exp ")" Stmt "else" Stmt
-> "if" "(" "a" ")" "if" "(" Exp ")" Stmt "else" "y" ";"
-> "if" "(" "a" ")" "if" "(" "b" ")" "x" ";" "else" "y" ";"
```

虽然都能抵达相同的目的地, 但我们走的路线却是不同的.

这会导致一些问题, 比如你使用 Bison 或 lalrpop 生成的 parser 会尝试根据 lexer 返回的 token 来规约得到 EBNF 中的非终结符. 你可以把规约理解成推导的逆过程, 所以对于上述 SysY 程序, parser 也能通过两种完全不同的方式进行语法的规约. 也就是说, 在这个过程中, 你可能会得到两棵完全不同的 AST——这就导致了 “二义性”, 你肯定不愿意看到这种情况的发生.

以上这个关于解析 `if/else` 的问题可以说相当之经典了, 甚至它还有一个单独的名字: 空悬 `else` 问题 ([dangling else problem](https://en.wikipedia.org/wiki/Dangling_else)). 为了避免这样的问题, SysY 的语义规定了 `else` 必须和最近的 `if` 进行匹配.

但是你可能会说: 这个问题都导致 parser 没法 “正常工作” 了, 编译器根本进行不到语义分析阶段, 在语法分析阶段就直接歇菜了, 那还怎么搞嘛. 其实这个问题是可以直接在语法层面解决的, 你只需对 `if/else` 的语法略加修改 (提示: 拆分), 就可以完全规避这个问题.

## 语义分析

无需新增内容. 记得对 `if/else` 的各部分 (条件和各分支) 进行语义分析即可.

## IR 生成

从本章开始, 你生成的程序的结构就不再是线性的了, 而是带有分支的. 在 [Lv1 中我们提到过](/lv1-main/ir-gen?id=koopa-ir-基础), Koopa IR 程序的结构按层次可以分为程序, 函数, 基本块和指令. 而你可以通过基本块和控制转移指令, 来在 Koopa IR 中表达分支的语义.

Koopa IR 中, 控制转移指令有两种:

1. **`br 条件, 目标1, 目标2` 指令:** 进行条件分支, 其中 `条件` 为整数, 两个目标为基本块. 如果 `条件` 非 0, 则跳转到 `目标1` 基本块的开头执行, 否则跳转到 `目标2`.
2. **`jump 目标` 指令:** 进行无条件跳转, 其中 `目标` 为基本块. 直接跳转到 `目标` 基本块的开头执行.

在之前的 Koopa IR 程序中, 只有一个入口基本块 `%entry`. 现在, 你可以通过划分新的基本块, 来标记控制流转移的目标.

示例程序生成的 Koopa IR 为:

```koopa
fun @main(): i32 {
%entry:
  @a = alloc i32
  store 2, @a
  // if 的条件判断部分
  %0 = load @a
  br %0, %then, %else

// if 语句的 if 分支
%then:
  %1 = load @a
  %2 = add %1, 1
  store %2, @a
  jump %end

// if 语句的 else 分支
%else:
  store 0, @a
  jump %end

// if 语句之后的内容, if/else 分支的交汇处
%end:
  %3 = load @a
  ret %3
}
```

需要注意的是, 基本块的结尾必须是 `br`, `jump` 或 `ret` 指令其中之一. 也就是说, 即使两个基本块是相邻的, 例如上述程序的 `%else` 基本块和 `%end` 基本块, 如果你想表达执行完前者之后执行后者的语义, 你也必须在前者基本块的结尾添加一条目标为后者的 `jump` 指令. 这点和汇编语言中 label 的概念有所不同.

?> 上述文本形式的 Koopa IR 程序中, 四个基本块看起来都是相邻的, 但实际转换到内存形式后, 这些基本块并不存在所谓的 “相邻” 关系. 它们之间通过控制转移指令, 建立了图状的拓扑关系, 即, 这些基本块构成了一个控制流图 ([control-flow graph](https://en.wikipedia.org/wiki/Control-flow_graph)).
<br><br>
编译器在大部分情况下都在处理诸如控制流图的图结构, 但一旦生成目标代码, 编译器就不得不把图结构压扁, 变成线性的结构——因为处理器从内存里加载程序到执行程序的过程中, 根本不存在 “图” 的概念. 这个压缩过程必然会损失很多信息, 这也是编译优化和体系结构之间存在的 gap.

## 目标代码生成

RISC-V 中也存在若干能表示分支和跳转的指令/伪指令, 你可以使用其中两条来翻译 Koopa IR 中的 `br` 和 `jump` 指令:

1. **`bnez 寄存器, 目标`:** 判断 `寄存器` 的值, 如果不为 0, 则跳转到目标, 否则继续执行下一条指令.
2. **`j 目标`:** 无条件跳转到 `目标`.

同时, 在 RISC-V 汇编中, 你可以使用 `名称:` 的形式来定义一个 label, 标记控制转移指令的目标.

示例程序生成的 RISC-V 汇编为:

```
  .text
  .globl main
main:
  addi sp, sp, -32
  li t0, 2
  sw t0, 0(sp)
  lw t0, 0(sp)
  sw t0, 4(sp)

  # if 的条件判断部分
  lw t0, 4(sp)
  bnez t0, then
  j else

  # if 语句的 if 分支
then:
  lw t0, 0(sp)
  sw t0, 8(sp)
  lw t0, 8(sp)
  li t1, 1
  add t0, t0, t1
  sw t0, 12(sp)
  lw t0, 12(sp)
  sw t0, 0(sp)
  j end

  # if 语句的 else 分支
else:
  li t0, 0
  sw t0, 0(sp)
  j end

  # if 语句之后的内容, if/else 分支的交汇处
end:
  lw t0, 0(sp)
  sw t0, 16(sp)
  lw a0, 16(sp)
  addi sp, sp, 32
  ret
```
