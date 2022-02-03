# Lv3.2. 算数表达式

本节新增/变更的语法规范如下:

```ebnf
Exp         ::= AddExp;
PrimaryExp  ::= ...;
Number      ::= ...;
UnaryExp    ::= ...;
UnaryOp     ::= ...;
MulExp      ::= UnaryExp | MulExp ("*" | "/" | "%") UnaryExp;
AddExp      ::= MulExp | AddExp ("+" | "-") MulExp;
```

## 一个例子

```c
int main() {
  return 1 + 2 * 3;
}
```

## 词法/语法分析

词法/语法分析部分同上一节, 你需要处理新增的运算符, 根据新增的语法规范设计新的 AST, 或者修改现有的 AST, 然后让你的 parser 支持新增的语法规范.

## 语义分析

暂无需要添加的内容.

## IR 生成

示例代码可以生成如下的 Koopa IR:

```koopa
fun @main(): i32 {
%entry:
  %0 = mul 2, 3
  %1 = add 1, %0
  ret %1
}
```

按照常识, `*`/`/`/`%` 运算符的优先级应该高于 `+`/`-` 运算符, 所以你生成的代码应该先计算乘法, 后计算加法. SysY 的语法规范中已经体现了运算符的优先级, 如果你正确建立了 AST, 那么你在后序遍历 AST 时, 生成的代码自然会是上述形式.

## 目标代码生成

关键部分的 RISC-V 汇编如下:

```
  li  t0, 2
  li  t1, 3
  mul t1, t0, t1
  li  t2, 1
  add t2, t1, t2
```
