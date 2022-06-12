# Lv2.2. 目标代码生成

之前, 你的编译器已经可以把:

```c
int main() {
  // 阿卡林
  return 0;
}
```

编译成如下的 Koopa IR 程序:

```koopa
fun @main(): i32 {
%entry:
  ret 0
}
```

我们的目标是, 进一步把它编译为:

```
  .text
  .globl main
main:
  li a0, 0
  ret
```

## 遍历内存形式的 IR

### C/C++ 实现

C/C++ 中, 得到 raw program 过后, 你可以遍历它的函数列表:

```c
koopa_raw_program_t raw = ...;
// 使用 for 循环遍历函数列表
for (size_t i = 0; i < raw.funcs.len; ++i) {
  // 正常情况下, 列表中的元素就是函数, 我们只不过是在确认这个事实
  // 当然, 你也可以基于 raw slice 的 kind, 实现一个通用的处理函数
  assert(raw.funcs.kind == KOOPA_RSIK_FUNCTION);
  // 获取当前函数
  koopa_raw_function_t func = (koopa_raw_function_t) raw.funcs.buffer[i];
  // 进一步处理当前函数
  // ...
}
```

对于示例程序, `raw.funcs.len` 一定是 `1`, 因为程序里显然只有一个函数. 进一步查看 `koopa.h` 中 `koopa_raw_function_t` 的定义, 我们据此可以遍历函数中所有的基本块:

```c
for (size_t j = 0; j < func->bbs.len; ++j) {
  assert(func->bbs.kind == KOOPA_RSIK_BASIC_BLOCK);
  koopa_raw_basic_block_t bb = (koopa_raw_basic_block_t) func->bbs.buffer[j];
  // 进一步处理当前基本块
  // ...
}
```

同样, 对于示例程序, `func->bbs.len` 也一定是 `1`, 因为 `@main` 函数内只有一个名为 `%entry` 的基本块. 遍历指令的方法与之类似, 此处不再赘述.

最后你应该可以得到一个 `koopa_raw_value_t`, 我们需要对其进行进一步处理:

```c
koopa_raw_value_t value = ...;
// 示例程序中, 你得到的 value 一定是一条 return 指令
assert(value->kind.tag == KOOPA_RVT_RETURN);
// 于是我们可以按照处理 return 指令的方式处理这个 value
// return 指令中, value 代表返回值
koopa_raw_value_t ret_value = value->kind.data.ret.value;
// 示例程序中, ret_value 一定是一个 integer
assert(ret_value->kind.tag == KOOPA_RVT_INTEGER);
// 于是我们可以按照处理 integer 的方式处理 ret_value
// integer 中, value 代表整数的数值
int32_t int_val = ret_value->kind.data.integer.value;
// 示例程序中, 这个数值一定是 0
assert(int_val == 0);
```

上述代码展示了在 C/C++ 中如何读取 raw program 中函数, 基本块和 return/integer 指令的数据, 相信你从中不难举一反三, 推导出访问其他指令的方法. 当然, 要想实现 “访问 Koopa IR” 的目标, 我们最好还是定义一系列对应的访问函数, 用 DFS 的思路来访问 raw program. 以 C++ 为例:

```cpp
// 函数声明略
// ...

// 访问 raw program
void Visit(const koopa_raw_program_t &program) {
  // 执行一些其他的必要操作
  // ...
  // 访问所有全局变量
  Visit(program.values);
  // 访问所有函数
  Visit(program.funcs);
}

// 访问 raw slice
void Visit(const koopa_raw_slice_t &slice) {
  for (size_t i = 0; i < slice.len; ++i) {
    auto ptr = slice.buffer[i];
    // 根据 slice 的 kind 决定将 ptr 视作何种元素
    switch (slice.kind) {
      case KOOPA_RSIK_FUNCTION:
        // 访问函数
        Visit(reinterpret_cast<koopa_raw_function_t>(ptr));
        break;
      case KOOPA_RSIK_BASIC_BLOCK:
        // 访问基本块
        Visit(reinterpret_cast<koopa_raw_basic_block_t>(ptr));
        break;
      case KOOPA_RSIK_VALUE:
        // 访问指令
        Visit(reinterpret_cast<koopa_raw_value_t>(ptr));
        break;
      default:
        // 我们暂时不会遇到其他内容, 于是不对其做任何处理
        assert(false);
    }
  }
}

// 访问函数
void Visit(const koopa_raw_function_t &func) {
  // 执行一些其他的必要操作
  // ...
  // 访问所有基本块
  Visit(func->bbs);
}

// 访问基本块
void Visit(const koopa_raw_basic_block_t &bb) {
  // 执行一些其他的必要操作
  // ...
  // 访问所有指令
  Visit(bb->insts);
}

// 访问指令
void Visit(const koopa_raw_value_t &value) {
  // 根据指令类型判断后续需要如何访问
  const auto &kind = value->kind;
  switch (kind.tag) {
    case KOOPA_RVT_RETURN:
      // 访问 return 指令
      Visit(kind.data.ret);
      break;
    case KOOPA_RVT_INTEGER:
      // 访问 integer 指令
      Visit(kind.data.integer);
      break;
    default:
      // 其他类型暂时遇不到
      assert(false);
  }
}

// 访问对应类型指令的函数定义略
// 视需求自行实现
// ...
```

相信从上述代码中, 你已经基本掌握了在 C/C++ 中遍历 raw program 的方法.

### Rust 实现

Rust 中对内存形式 Koopa IR 的处理方式和 C/C++ 大同小异: 都是遍历列表, 然后根据类型处理其中的元素. 比如得到 `Program` 后, 你同样可以遍历其中的函数列表:

```rust
let program = ...;
for &func in program.func_layout() {
  // 进一步访问函数
  // ...
}
```

但需要注意的是, 在 Koopa IR 的内存形式中, “IR 的数据” 和 “IR 的 layout” 是彼此分离表示的.

?> “Layout” 直译的话是 “布局”. 这个词不太好用中文解释, 虽然 Koopa IR 的相关代码确实是我写的, 我也確實是個平時講中文的中國大陸北方網友.
<br><br>
比如对于基本块的指令列表: 指令的数据并没有直接按照指令出现的顺序存储在列表中. 指令的数据被统一存放在函数内的一个叫做 `DataFlowGraph` 的结构中, 同时每个指令具有一个指令 ID (或者也可以叫 handle), 你可以通过 ID 在这个结构中获取对应的指令. 指令的列表中存放的其实是指令的 ID.
<br><br>
这么做看起来多套了一层, 但实际上 “指令 ID” 和 “指令数据” 的对应关系, 就像 C/C++ 中 “指针” 和 “指针所指向的内存” 的对应关系, 理解起来并不复杂. 至于为什么不直接把数据放在列表里? 为什么不用指针或者引用来代替 “指令 ID”? 如果对 Rust 有一定的了解, 你应该会知道这么做的后果...

所以, 此处你可以通过遍历 `func_layout`, 来按照程序中函数出现的顺序来获取函数 ID, 然后据此从程序中拿到函数的数据, 进行后续访问:

```rust
for &func in program.func_layout() {
  let func_data = program.func(func);
  // 访问函数
  // ...
}
```

访问基本块和指令也与之类似, 但需要注意: 基本块的数据里没有指令列表, 只有基本块的名称之类的信息. 基本块的指令列表在函数的 layout 里.

```rust
// 遍历基本块列表
for (&bb, node) in func_data.layout().bbs() {
  // 一些必要的处理
  // ...
  // 遍历指令列表
  for &inst in node.insts().keys() {
    let value_data = func_data.dfg().value(inst);
    // 访问指令
    // ...
  }
}
```

指令的数据里记录了指令的具体种类, 你可以通过模式匹配来处理你感兴趣的指令:

```rust
use koopa::ir::ValueKind;
match value_data.kind() {
  ValueKind::Integer(int) => {
    // 处理 integer 指令
    // ...
  }
  ValueKind::Return(ret) => {
    // 处理 ret 指令
    // ...
  }
  // 其他种类暂时遇不到
  _ => unreachable!(),
}
```

如需遍历访问 Koopa IR, 你同样需要将程序实现成 DFS 的模式. 此处推荐通过为内存形式 IR 扩展 trait 来实现这一功能:

```rust
// 根据内存形式 Koopa IR 生成汇编
trait GenerateAsm {
  fn generate(&self, /* 其他必要的参数 */);
}

impl GenerateAsm for koopa::ir::Program {
  fn generate(&self) {
    for &func in program.func_layout() {
      program.func(func).generate();
    }
  }
}

impl GenerateAsm for koopa::ir::FunctionData {
  fn generate(&self) {
    // ...
  }
}
```

## 生成汇编

生成汇编的思路和生成 Koopa IR 的思路类似, 都是遍历数据结构, 输出字符串. 此处不做过多赘述. 不过我们依然需要解释一下, 你生成的 RISC-V 汇编到底做了哪些事情.

在 SysY 程序中, 我们定义了一个 `main` 函数, 这个函数什么也没做, 只是返回了一个整数, 之后就退出了. RISC-V 程序所做的事情与之一致:

1. 定义了 `main` 函数.
2. 将作为返回值的整数加载到了存放返回值的寄存器中.
3. 执行返回指令.

所以你需要知道几件事:

* **如何定义函数?**
  * 所谓函数, 从处理器的角度看只不过是一段指令序列. 调用函数时处理器跳转到序列的入口执行, 执行到序列中含义是 “函数返回” 的指令时, 处理器退出函数, 回到调用函数前的指令序列继续执行.
  * 在汇编层面 “定义” 函数, 其实只需要标注这个序列的入口在什么位置即可, 其余函数返回之类的操作都属于函数内的指令要完成的事情.
* **RISC-V 中如何设置返回值?**
  * RISC-V 指令系统的 ABI 规定, 返回值应当被存入 `a0` 和 `a1` 寄存器中. RV32I 下, 寄存器宽度为 32 位, 所以用寄存器可以传递两个 32 位的返回值.
  * 在编译实践涉及的所有情况下, 函数的返回值只有 32 位. 所以我们在传递返回值时, 只需要把数据放入 `a0` 寄存器即可.
* **如何将整数加载到寄存器中?**
  * RISC-V 的汇编器支持 `li` 伪指令. 这条伪指令的作用是加载立即数 (**l**oad **i**mmediate) 到指定的寄存器中.

所以你输出的汇编的含义其实是:

```
  .text         # 声明之后的数据需要被放入代码段中
  .globl main   # 声明全局符号 main, 以便链接器处理
main:           # 标记 main 的入口点
  li a0, 0      # 将整数 0 加载到存放返回值的 a0 寄存器中
  ret           # 返回
```

关于 RISC-V 指令的官方定义, 请参考 [RISC-V 的规范](https://github.com/riscv/riscv-isa-manual/releases/download/Ratified-IMAFDQC/riscv-spec-20191213.pdf). 当然, 我们整理了编译实践中需要用到的 RISC-V 指令的相关定义, 你可以参考 [RISC-V 指令速查](/misc-app-ref/riscv-insts).

最后的最后, 有时你可能实在不清楚, 对于某段特定的 C/SysY 程序, 编译器到底应该输出什么样的 RISC-V 汇编. 此时你可以去 [Compiler Explorer](https://godbolt.org/) 这个网站, 该网站可以很方便地查看某种编译器编译某段 C 程序后究竟会输出何种汇编.

你可以在网站右侧的汇编输出窗口选择使用 “RISC-V rv32gc clang (trunk)” 编译器, 然后将编译选项设置为 `-O3 -g0`, 并查看窗口内的汇编输出.
