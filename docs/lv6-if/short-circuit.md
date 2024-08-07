# Lv6.2. 短路求值

本节没有任何语法规范上的变化.

## 一个例子

```c
int main() {
  int a = 0, b = 1;
  if (a || b) {
    a = a + b;
  }
  return a;
}
```

## 词法/语法分析

因为语法规范不变, 所以这部分没有需要改动的内容.

## 语义分析

同上, 暂无需要改动的内容.

## IR 生成

SysY 程序中的逻辑运算符, 即 `||` 和 `&&`, 在求值时遵循短路求值的语义. 所谓短路求值, 指的是, 求值逻辑表达式时先计算表达式的左边 (left-hand side, LHS), 如果表达式左左边的结果已经可以确定整个表达式的计算结果, 就不再计算表达式的右边 (right-hand side, RHS).

比如对于一个 `||` 表达式, 如果 LHS 的值是 1, 根据或运算的性质, 无论 RHS 求出何值, 整个表达式的求值结果一定是 1, 所以此时就不再计算 RHS 了. `&&` 表达式同理.

编译器实现短路求值的思路, 其实和上述思路没什么区别. 例如, 短路求值 `lhs || rhs` 本质上做了这个操作:

```c
int result = 1;
if (lhs == 0) {
  result = rhs != 0;
}
// 表达式的结果即是 result
```

你的编译器可以按照上述思路, 在生成 IR 时, 把逻辑表达式翻译成若干分支, 跳转和赋值.

当然, 目前对逻辑表达式进行短路求值和进行非短路求值是没有任何区别的, 要想体现这一区别, RHS 必须是一个带有副作用 ([side effect](https://en.wikipedia.org/wiki/Side_effect_(computer_science))) 的表达式. 而 SysY 中, 仅有包含函数调用的表达式才可能产生副作用, 例如调用了一个可能修改全局变量的函数, 或可能进行 I/O 操作的函数, 等等. 但为了你的编译器顺利通过之后的测试, 你必须正确实现这一功能.

短路求值逻辑表达式有什么用呢? 首先它能剔除很多不必要的计算, 例如表达式的 RHS 进行了一个非常耗时的计算, 如果编程语言支持短路求值, 在求出 LHS 就能确定逻辑表达式结果的情况下, 计算机就不必劳神再把 RHS 算一遍了. 此外, 利用短路求值的性质, 你可以简化某些程序的写法, 例如在 C/C++ 中可以这么写:

```cpp
void *ptr = ...;
if (ptr != nullptr && check(ptr)) {
  // 执行一些操作
  // ...
}
```

编译器会保证函数 `check` 被调用时, 指针 `ptr` 一定非空, 此时 `check` 函数可以放心地解引用指针而不必担心段错误.

## 目标代码生成

本节并未用到新的 Koopa IR 指令, 也不涉及 Koopa IR 中的新概念, 所以这部分没有需要改动的内容.
