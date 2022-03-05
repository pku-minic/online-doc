# Lv9.1. 一维数组

本节新增/变更的语法规范如下:

```ebnf
ConstDef      ::= IDENT ["[" ConstExp "]"] "=" ConstInitVal;
ConstInitVal  ::= ConstExp | "{" [ConstExp {"," ConstExp}] "}";
VarDef        ::= IDENT ["[" ConstExp "]"]
                | IDENT ["[" ConstExp "]"] "=" InitVal;
InitVal       ::= Exp | "{" [Exp {"," Exp}] "}";

LVal          ::= IDENT ["[" Exp "]"];
```

## 一个例子

```c
int x[2] = {10, 20};

int main() {
  int arr[5] = {1, 2, 3};
  return arr[2];
}
```

## 词法/语法分析

针对本节发生变化的语法规则, 设计新的 AST, 并更新你的 parser 实现即可.

## 语义分析

数组定义时, 数组长度使用 `ConstExp` 表示, 所以你在编译时必须求出代表数组长度的常量表达式. 同时, 对于全局数组变量, 语义规定它的初始值也必须是常量表达式, 你也需要对其求值.

需要注意的是, 常量求值时, 你应该只考虑整数类型的常量定义, **而不要求值常量数组**. 例如:

```c
const int a = 10;
const int arr[2] = {1, 2};
```

对于常量 `a`, 你的编译器应该在语义分析阶段把它求出来, 存入符号表. 对于常量 `arr`, 你的编译器只需要将其初始化表达式中的常量算出来, 但不需要再设计一种代表数组常量的数据结构并将其存入符号表. 在生成的 IR 中, `a` 是不存在的 (全部被替换成了常量); 而 `arr` 是存在的, 体现在 IR 中就是一个数组.

综上所述, 如果你在常量表达式中扫描到了对常量数组的解引用, 你可以将其视为发生了语义错误. 例如如下 SysY 程序是存在语义错误的:

```c
// 允许定义常量数组, 此时数组 arr 不能被修改
const int arr[2] = {1, 2};
// arr 本身不会参与编译期求值, 所以编译器无法在编译时算出 arr[1] 的值
// 所以此处出现了语义错误
const int a = 1 + arr[1];
```

此外, 由于引入了数组定义, 变量的类型将不再是单一的整数. 所以你需要考虑在语义分析阶段加入类型检查机制, 来避免某些语义错误的情况发生, 例如:

```c
int arr[10];
// 类型不匹配
int a = arr;
```

当然, 再次重申, 为了降低难度, 测试/评测时我们提供的输入都是合法的 SysY 程序, 并不会出现语义错误. 你的编译器不进行类型检查也是可以的.

## IR 生成

数组的定义和变量的定义类似, 同样使用 `alloc` 指令完成, 不过之后的类型需要换成数组类型. Koopa IR 中, `[T, len]` 可以表示一个元素类型为 `T`, 长度为 `len` 的数组类型. 例如 `[i32, 3]` 对应了 SysY 中的 `int[3]`, `[[i32, 3], 2]` 对应了 SysY 中的 `int[2][3]` (注意这里的 2 和 3 是反着的).

SysY 中数组相关的操作通常包含两步: 通过 `[i]` 定位数组的元素, 然后读写这个元素. 根据写 C/C++ 时积累的经验, 你不难发现, 这种操作本质上其实是指针计算. 在 Koopa IR 中, 针对数组的指针计算可以使用 `getelemptr` 指令完成.

`getelemptr` 指令的用法类似于 `getelemptr 指针, 偏移量`. 其中, `指针` 必须是一个数组类型的指针, 比如 `*[i32, 3]`, 或者 `*[[i32, 3], 2]`. 我们在 Lv4 中提到, `alloc T` 指令返回的类型是 `T` 的指针, 所以 `alloc` 数组时, 你刚好就可以得到一个数组的指针.

`getelemptr ptr, index` 指令执行了如下操作: 假设指针 `ptr` 的类型是 `*[T, N]`, 指令会算出一个新的指针, 这个指针的值是 `ptr + index * sizeof(T)`, 类型是 `*T`. 在逻辑上, 这种操作和 C 语言中的数组访问操作是完全一致的. 比如:

```c
int arr[2];
arr[1];
```

翻译到 Koopa IR 就是:

```koopa
@arr = alloc [i32, 2]       // @arr 的类型是 *[i32, 2]
%ptr = getelemptr @arr, 1   // %ptr 的类型是 *i32
%value = load %ptr          // %value 的类型是 i32
// 这是一段类型和功能都正确的 Koopa IR 代码
```

本质上相当于:

```c
int arr[2];
// 在 C 语言的指针运算中, int 指针加 1
// 就相当于对指针指向的地址的数值加了 1 * sizeof(int)
int *ptr = arr + 1;
*ptr;
```

对于多维数组也是一样, 虽然本节你暂时不需要实现多维数组:

```c
int arr[2][3];
arr[1][2];
```

翻译到 Koopa IR 就是:

```koopa
@arr = alloc [[i32, 3], 2]    // @arr 的类型是 *[[i32, 3], 2]
%ptr1 = getelemptr @arr, 1    // %ptr1 的类型是 *[i32, 3]
%ptr2 = getelemptr @arr, 2    // %ptr2 的类型是 *i32
%value = load %ptr2           // %value 的类型是 i32
// 这是一段类型和功能都正确的 Koopa IR 代码
```

`getelemptr` 得到的是一个指针, 指针既可以被 `load`, 也可以被 `store`. 所以, 你的编译器可以通过生成 `getelemptr` 和 `store` 的方法, 来处理 SysY 中写入数组元素的操作. 以此类推, 对于局部数组变量的初始化列表, 你也可以把它编译成若干指针计算和 `store` 的形式. 但是, 你可能会问: 全局数组变量的初始化要怎么处理呢?

确实, Koopa IR 的全局作用域内是不能出现 `store` 指令的. 因为对应到汇编层面, 并不存在一段可以在程序被操作系统加载的时候执行的代码, 并让它帮你执行一系列的 `store` 操作. 操作系统加载程序的时候, 会把可执行文件中各段 (segment) 对应的数据, 逐步复制到内存中. 所以, 如果我们能把数组初始化列表里的元素表示成数据的形式, 我们就可以实现全局数组初始化.

这在 SysY 中是完全可行的, 因为语义规定, 全局数组变量的初始化列表中只能出现常量表达式, 所以你的编译器一定能在编译时把初始化列表里的每个元素都确定下来. 既然你已经预先知道了所有的元素, 你的编译器就可以把它们写死成数据, 然后在生成汇编的时候用 `.word` 之类的 directive 告诉汇编器, 把这些数据塞进数据段.

Koopa IR 中, 你可以使用 “aggregate” 常量来表示一个常量的数组初始化列表, 比如:

```c
// 这是个全局数组
int arr[3] = {1, 2, 3};
```

翻译到 Koopa IR 就是:

```koopa
globl @arr = alloc [i32, 3], {1, 2, 3}
```

Aggregate 中出现的元素必须为彼此之间类型相同的常量, 比如整数, `zeroinit`, 或者另一个 aggregate, 所以多维数组也可以用这种方式初始化. 此外, aggregate 中不能省略任何元素, 对于如下 SysY 程序:

```c
// 这是个全局数组
int arr[3] = {5};
```

你的编译器必须将其翻译为:

```koopa
global @arr = alloc [i32, 3], {5, 0, 0}
```

之前提到, Koopa IR 是强类型 IR, 且能够自动推导部分类型. 假设 aggregate 中各元素的类型为 `T`, 且总共有 `len` 个元素, 那么 aggregate 本身的类型就会被推导为 `[T, len]`. 所以:

```koopa
// 如下 Koopa IR 指令不合法的原因是, alloc 的类型和初始化类型不符
// 右边的 aggregate 的类型为 [i32, 1]
global @arr = alloc [i32, 3], {5}
```

最后, 以防你忘了, 多提一句: `zeroinit` 也是可以用来零初始化数组的:

```koopa
// 相当于 SysY 中的全局数组 int zeroed_array[2048];
global @zeroed_array = alloc [i32, 2048], zeroinit
```

最后的最后, 你可能会问: 既然我能在全局数组初始化的时候使用 aggregate/`zeroinit`, 那我能不能在局部变量初始化的时候也这么用呢? 答案是可以:

```koopa
@arr = alloc [i32, 5]
store {1, 2, 3, 0, 0}, @arr
```

但这么搞的话, 你的编译器需要在目标代码生成的时候进行一些额外的处理.

综上所述, 示例程序生成的 Koopa IR 为:

```koopa
global @x = alloc [i32, 2], {10, 20}

fun @main(): i32 {
%entry:
  @arr = alloc [i32, 5]
  // arr 的初始化列表, 别忘了补 0 这个事
  %0 = getelemptr @arr, 0
  store 1, %0
  %1 = getelemptr @arr, 1
  store 2, %1
  %2 = getelemptr @arr, 2
  store 3, %2
  %3 = getelemptr @arr, 3
  store 0, %3
  %4 = getelemptr @arr, 4
  store 0, %4

  %5 = getelemptr @arr, 2
  %6 = load %5
  ret %6
}
```

## 目标代码生成

本节生成的 Koopa IR 中出现了若干新概念, 下面我们来逐一过一下.

### 计算类型大小

要想进行内存分配, 你的编译器必须先算出应分配的内存的大小. `alloc` 指令中出现了不同于 `i32` 的数组类型, 以及 `getelemptr` 的返回值是个指针, 它们的大小自然也是需要计算出来的. 这其中, 指针的大小在 RV32I 上就是 4 字节, 毕竟 RV32I 是 32 位的指令系统. 而数组类型的大小, 我应该不用多提了, 大家不难通过几次乘法算出这个数值.

C/C++ 中, Koopa IR 类型在内存中表示为 `koopa_raw_type_t`, 你可以 DFS 遍历其内容, 并按照我们提到的规则计算得到类型的大小. Rust 中, `Type` 提供了 `size()` 方法, 这个方法会用 DFS 遍历的方式帮你求出类型的大小.

但需要注意的是, 考虑到 Koopa IR 的泛用性 (比如搞不好你哪天心血来潮想给 Koopa IR 写个 x86-64 后端), 默认情况下, Rust 的 `koopa` crate 中的 `Type::size()` 会按照当前平台的指针大小来计算指针类型的大小. 因为目前大家用的基本都是 64 位平台, 所以在遇到指针类型时, `size()` 会返回 8. 为了适配 riscv32 的指针宽度, 你需要在进行代码生成前 (比如在 `main` 里), 调用 `Type::set_ptr_size(4)`, 来设置指针类型的大小为 4 字节.

### 处理 `getelemptr`

前文已经描述过 `getelemptr` 的含义了, 无非是做了一次乘法和加法. 所以, 对于如下 Koopa IR 程序:

```koopa
@arr = alloc [i32, 2]
%ptr = getelemptr @arr, 1
```

假设 `@arr` 位于 `sp + 4`, 则对应的 RISC-V 汇编可以是:

```
  # 计算 @arr 的地址
  addi t0, sp, 4
  # 计算 getelemptr 的偏移量
  li t1, 1
  li t2, 4
  mul t1, t1, t2
  # 计算 getelemptr 的结果
  add t0, t0, t1
  # 保存结果到栈帧
  # ...
```

注意:

1. 检查 `addi` 中立即数的范围.
2. 上述 RISC-V 汇编并非是最优的. 对于偏移量是 2 的整数次幂的情况, 你可以用移位指令来替换乘法指令.
3. 对于全局数组变量的指针运算, 代码生成方式和上述类似, 只不过你需要用 `la` 加载全局变量的地址.

### 处理全局初始化

之前章节解释过如何在全局生成 `zeroinit` 和整数常量: 对于前者, 生成一个 `.zero sizeof(T)`, 其中 `sizeof(T)` 代表 `zeroinit` 的类型的大小. 对于后者, 生成一个 `.word 整数`.

Aggregate 的生成方式就是把上述内容组合起来, 比如:

```koopa
global @arr = alloc [i32, 3], {1, 2, 3}
```

生成的 RISC-V 汇编为:

```
  .data
  .globl arr
arr:
  .word 1
  .word 2
  .word 3
```

### 生成代码

在理解上述概念之后, 你不难自行完成目标代码的生成, 故此处不再赘述.
