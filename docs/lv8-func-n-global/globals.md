# Lv8.3. 全局变量和常量

本节新增/变更的语法规范如下:

```ebnf
CompUnit ::= [CompUnit] (Decl | FuncDef);
```

## 一个例子

```c
int var;

const int one = 1;

int main() {
  return var + one;
}
```

## 词法/语法分析

本节中, 语法规则 `CompUnit` 发生了变化, 你可能需要为其设计新的 AST, 并更新你的 parser 实现.

## 语义分析

本节 `CompUnit` 的定义较上一节又发生了变化, 不仅允许多个函数存在于全局范围内, 还允许变量/常量声明存在于全局范围内. 你需要把所有全局范围内的声明, 都放在全局作用域中.

此外, 全局常量和局部常量一样, 都需要在编译期求值. 你的编译器在处理全局常量时, 需要扫描它的初始值, 并直接算出结果, 存入符号表.

## IR 生成

对于所有全局变量, 你的编译器应该生成全局内存分配指令 (`global alloc`). 这种指令的用法和 `alloc` 类似, 区别是全局分配必须带初始值.

示例程序生成的 Koopa IR 为:

```koopa
global @var = alloc i32, zeroinit

fun @main(): i32 {
%entry:
  %0 = load @var
  %1 = add %0, 1
  ret %1
}
```

未初始化的全局变量的值为 0, 所以我们使用 `zeroinit` 作为初始值, 初始化了全局内存分配 `@var`.

此处的 `zeroinit` 代表零初始化器 (zero initializer). `zeroinit` 是一个通用的 0 值, 它可以是多种类型的. 不管是向 `i32` 类型的 `alloc` 中写入 `zeroinit`, 还是向你将在 Lv9 中遇到的数组类型的 `alloc` 中写入 `zeroinit`, 这些 `alloc` 分配的内存都会被填充 0.

当然, 对于这个示例, 你写 `global @var = alloc i32, 0` 也完全没问题.

## 目标代码生成

在操作系统层面, 局部变量和全局变量的内存分配是不同的. 前者的内存空间在程序运行时, 由函数在栈上动态开辟出来, 或者直接放在寄存器里. 后者在程序被操作系统加载时, 由操作系统根据可执行文件 (比如 [PE/COFF](https://en.wikipedia.org/wiki/Portable_Executable), [ELF](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format) 或 [Mach-O](https://en.wikipedia.org/wiki/Mach-O)) 中定义的 layout, 静态映射到虚拟地址空间, 进而映射到物理页上.

体现在 RISC-V 汇编中, 局部变量和全局变量的描述方式也有所区别. 前者的描述方式你已经见识过了, 基本属于润物细无声级别的: 你需要在函数中操作一下 `sp`, 然后搞几个偏移量, 再 `lw`/`sw`, 总体来说比较抽象. 后者就很直接了, 我们先看示例程序生成的 RISC-V 汇编:

```
  .data
  .globl var
var:
  .zero 4

  .text
  .globl main
main:
  addi sp, sp, -16
  la t0, var
  lw t0, 0(t0)
  sw t0, 0(sp)
  lw t0, 0(sp)
  li t1, 1
  add t0, t0, t1
  sw t0, 4(sp)
  lw a0, 4(sp)
  addi sp, sp, 16
  ret
```

这段汇编代码中, `.data` 是汇编器定义的一个 “directive”——你可以理解成一种特殊的语句. `.data` 指定汇编器把之后的所有内容都放到数据段 ([data segment](https://en.wikipedia.org/wiki/Data_segment)). 对操作系统来说, 数据段对应的内存里放着的所有东西都会被视作数据, 程序一般会把全局变量之类的内容都塞进数据段.

`.data` 之后的 `.zero` 也同样是一个 directive——事实上, 汇编程序中所有 `.` 开头的语句基本都是 directive. `.zero 4` 代表往当前地址处 (这里代表 `var` 对应的地址) 填充 4 字节的 0, 这对应了 Koopa IR 中的 `zeroinit`. 如果 Koopa IR 是以下这种写法:

```koopa
global @var = alloc i32, 233
```

那我们就应该使用 `.word 233` 这个 directive, 这代表往当前地址处填充机器字长宽度 (4 字节) 的整数 `233`.

于是现在, 你可能已经明白 `main` 之前的 `.text` 代表什么含义了: 它表示之后的内容应该被汇编器放到代码段 ([code segment](https://en.wikipedia.org/wiki/Code_segment)). 代码段和数据段的区别是, 代码段里的 “数据” 是只读且可执行的, 数据段里的数据可读可写但不可执行. 顺便一提, 这种 “可执行/不可执行” 的特性, 是操作系统加载可执行文件到虚拟地址空间时, 通过设置页表中虚拟页的权限位来实现的, 处理器将负责保证权限的正确性.

除了代码段和数据段, 可执行文件里通常还会有很多其他的段: 比如 `bss` 段存放需要零初始化的数据, 操作系统加载 `bss` 时会自动将其清零, 所以可执行文件中只保存 `bss` 的长度而不保存数据, 可以节省一些体积; `rodata` 段存放只读的数据 (**r**ead-**o**nly **data**). 其实这么看, 示例程序里的 `var` 放在 `bss` 段是最合适的, 但为了简化编译器的实现, 你可以把它放在 `data` 段.

全局变量的内存分配完毕之后, 我们要怎么访问到这块内存呢? 你可以注意到在 `main` 里出现了一条 `la t0, var` 指令 (其实是伪指令), 这条指令会把符号 `var` 对应的地址加载到 `t0` 寄存器中. 之后的 `lw` 指令以 `t0` 为地址, 读取了 4 字节数据到 `t0`. 这两条指令共同完成了加载全局变量的操作.

?> `la` 伪指令之后的符号并不只局限在数据段, 其他段中符号的地址也是可以被加载的. 你可以尝试使用 RISC-V 汇编实现一个简单的程序, 读取 `main` 函数的第一条指令的值并输出, 然后对照 [RISC-V 规范](https://github.com/riscv/riscv-isa-manual/releases/download/Ratified-IMAFDQC/riscv-spec-20191213.pdf), 查看这条指令是否对应了你在汇编中所写的那条指令.
