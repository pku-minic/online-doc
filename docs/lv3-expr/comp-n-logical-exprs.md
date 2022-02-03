# Lv3.3. 比较和逻辑表达式

本节新增/变更的语法规范如下:

```ebnf
Exp         ::= LOrExp;
PrimaryExp  ::= ...;
Number      ::= ...;
UnaryExp    ::= ...;
UnaryOp     ::= ...;
MulExp      ::= ...;
AddExp      ::= ...;
RelExp      ::= AddExp | RelExp ("<" | ">" | "<=" | ">=") AddExp;
EqExp       ::= RelExp | EqExp ("==" | "!=") RelExp;
LAndExp     ::= EqExp | LAndExp "&&" EqExp;
LOrExp      ::= LAndExp | LOrExp "||" LAndExp;
```

## 一个例子

```c
int main() {
  return 1 <= 2;
}
```

## 词法/语法分析

同上一节. 但需要注意的是, 本节出现了一些两个字符的运算符, 比如例子中的 `<=`. 你需要修改 lexer 来适配这一更改.

## 语义分析

暂无需要添加的内容.

## IR 生成

示例代码可以生成如下的 Koopa IR:

```koopa
fun @main(): i32 {
%entry:
  %0 = le 1, 2
  ret %0
}
```

## 目标代码生成

关键部分的 RISC-V 汇编如下:

```
  li    t0, 1
  li    t1, 2
  # 执行小于等于操作
  sgt   t1, t0, t1
  seqz  t1, t1
```

如果你查阅 [RISC-V 规范](https://github.com/riscv/riscv-isa-manual/releases/download/Ratified-IMAFDQC/riscv-spec-20191213.pdf) 第 24 章 (Instruction Set Listings, 130 页), 你会发现 RISC-V 只支持小于指令 (`slt` 等). 而上述汇编中出现的 `sgt` 是一个伪指令, 也就是说, 这条指令并不真实存在, 而是用其他指令实现的.

已知, `slt t0, t1, t2` 指令的含义是, 判断寄存器 `t1` 的值是否小于 `t2` 的值, 并将结果 (0 或 1) 写入 `t0` 寄存器. 思考:

* `sgt t0, t1, t2` (判断大于) 是怎么实现的?
* 上述汇编中判断小于等于的原理是什么?
* 如何使用 RISC-V 汇编判断大于等于?

你可以使用 [Lv2 提到的方法](/lv2-code-gen/code-gen?id=生成汇编), 看看 Clang 是如何将这些运算翻译成 RISC-V 汇编的, 比如[这个例子](https://godbolt.org/z/59bxe767c).
