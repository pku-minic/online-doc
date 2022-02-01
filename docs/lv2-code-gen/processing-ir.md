# Lv2.1. 处理 Koopa IR

本节将引导你在上一章的基础上, 建立内存形式的 Koopa IR, 并在程序中访问这些数据结构.

## 建立内存形式的 Koopa IR

上一章中, 你的编译器已经可以输出 Koopa IR 程序了. 你可能会采用两种思路完成这一操作:

1. 遍历 AST, 输出文本形式的 Koopa IR 程序.
2. 遍历 AST, 直接建立 (某种) 内存形式的 Koopa IR, 再将其转换为文本形式输出.

对于第二种思路, 无论你是通过阅读 Koopa IR 的[文档](https://docs.rs/koopa), 直接建立了内存形式 IR, 还是根据[Koopa IR 规范](/misc-app-ref/koopa), 自行设计了一套数据结构来表示 Koopa IR 程序, 你其实都已经得到了一个可被你程序处理的内存形式的 Koopa IR. 在目标代码生成阶段, 你可以直接让你的编译器遍历这些数据结构, 并生成代码. **此时, 你可以跳过本节.**

第一种思路可能是大部分同学会采用的思路, 因为它相当简单且直观, 实现难度很低. 但其缺点是, 你在生成目标代码之前, 不得不再次将文本形式的 Koopa IR 转换成某种数据结构——这相当于再写一个编译器. 否则, 你的程序几乎无法直接基于文本形式 IR 生成汇编.

不过好在, 我们为大家提供了能够处理 Koopa IR 的库, 你可以使用其中的实现, 来将文本形式的 IR 转换为内存形式.

## C/C++ 实现

你可以使用 `libkoopa` 中的接口将文本形式 Koopa IR 转换为 raw program, 后者是 C/C++ 可以直接操作的, 由各种 `struct`, `union` 和指针组成的, 表示 Koopa IR 的数据结构.

首先你需要在代码中引用 `libkoopa` 的头文件:

```cpp
#include "koopa.h"
```

然后, 假设你生成的 Koopa IR 程序保存在了字符串 (类型为 `const char *`) `str` 中, 你可以执行:

```cpp
// 解析字符串 str, 得到 Koopa IR 程序
koopa_program_t program;
koopa_error_code_t ret = koopa_parse_from_string(str, &program);
assert(ret == KOOPA_EC_SUCCESS);  // 确保解析时没有出错
// 创建一个 raw program builder, 用来构建 raw program
koopa_raw_program_builder_t builder = koopa_new_raw_program_builder();
// 将 Koopa IR 程序转换为 raw program
koopa_raw_program_t raw = koopa_build_raw_program(builder, program);
// 释放 Koopa IR 程序占用的内存
koopa_delete_program(program);

// 处理 raw program
// ...

// 处理完成, 释放 raw program builder 占用的内存
// 注意, raw program 中所有的指针指向的内存均为 raw program builder 的内存
// 所以不要在 raw program builder 处理完毕之前释放 builder
koopa_delete_raw_program_builder(builder);
```

其中, raw program 的结构和我们在 Lv1 中提到的 Koopa IR 程序的结构完全一致:

* 最上层是 `koopa_raw_program_t`, 也就是 `Program`.
* 之下是全局变量定义列表和函数定义列表.
  * 在 raw program 中, 列表的类型是 `koopa_raw_slice_t`.
  * 本质上这是一个指针数组, 其中的 `buffer` 字段记录了指针数组的地址 (类型是 `const void **`), `len` 字段记录了指针数组的长度, `kind` 字段记录了数组元素是何种类型的指针
  * 在访问时, 你可以通过 `slice.buffer[i]` 拿到列表元素的指针, 然后通过判断 `kind` 来决定把这个指针转换成什么类型.
* `koopa_raw_function_t` 代表函数, 其中是基本块列表.
* `koopa_raw_basic_block_t` 代表基本块, 其中是指令列表.
* `koopa_raw_value_t` 代表全局变量, 或者基本块中的指令.

如果你的项目基于我们提供的 Make/CMake 模板, 则测试脚本/评测平台编译你的项目时, 会自动链接 `libkoopa`, 你无需为此操心.

如果你在编码时需要让编辑器/IDE 识别 `koopa.h` 文件中的声明, 你可以在 `libkoopa` 的仓库中获取到[这个头文件](https://github.com/pku-minic/koopa/blob/master/crates/libkoopa/include/koopa.h). 同时, 头文件中包含了所有 raw program 相关的数据结构的定义 (含详细注释), 你可以通过 RTFSC 来进一步了解 raw program 的结构.

## Rust 实现

你可以使用 `koopa` 这个 crate 来处理 Koopa IR. 请根据 [crates.io](https://crates.io/crates/koopa) 上的说明, 在你的项目中添加最新版本的 `koopa` 的依赖.

假设你生成的 Koopa IR 程序保存在了字符串 `s` 中, 你可以执行:

```rust
let driver = koopa::front::Driver::from(s);
let program = driver.generate_program().unwrap();
```

来得到一个内存形式的 Koopa IR 程序. 这个程序的结构和 Lv1 中的描述完全一致, 详情请参考[文档](https://docs.rs/koopa/0.0.3/koopa/ir/entities/struct.Program.html).
