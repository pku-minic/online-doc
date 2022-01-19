# 实验环境使用说明

## 配置实验环境

见 [Lv0.1 配置 Docker](/lv0-env-config/docker).

## 进入实验环境的命令行

你可以执行如下命令来进入实验环境的命令行:

```
docker run -it --rm compiler-dev bash
```

如果你希望把自己的编译器项目目录挂载到容器中 (大部分情况下都需要这么做), 你可以执行:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev bash
```

此时你本地的项目目录会出现在容器的 `/root/compiler` 目录中.

如果你希望在容器中使用调试器 (例如容器内的 `lldb`) 调试程序, 你应该:

```
docker run -it --rm -v 项目目录:/root/compiler \
  --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
  compiler-dev bash
```

## 准备你的编译器

为了保证测试的正常进行, 你的编译器必须符合下列要求:

### 项目要求

你可以使用 C/C++/Rust 来实现你的编译器, 同时为了方便测试程序在测试时编译你的编译器项目, 项目的根目录中必须存在下列三种文件之一:

* **`Makefile` 或 `makefile` 文件:** 测试程序将使用 `make BUILD_DIR="build目录的路径" -C "项目路径"` 命令编译项目. 你的 `Makefile` 必须依据 `BUILD_DIR` 参数的值, 将生成的可执行文件输出到该路径中, 并命名为 `compiler`.
* **`CMakeLists.txt` 文件:** 测试程序将使用 `cmake -S "项目路径" -B "build目录的路径" && cmake --build "build目录的路径"` 命令编译项目. 你的 `CMakeLists.txt` 必须将可执行文件直接输出到所指定的 `build` 目录的根目录, 且将其命名为 `compiler`.
* **`Cargo.toml` 文件:** 测试程序将使用 `cargo build --manifest-path "Cargo.toml的路径" --release` 命令编译项目. 你无需担心任何其他内容.

### 输入形式

编译器必须能够读取如下格式的命令行参数 (**假设**你的编译器名字叫做 `compiler`):

```
compiler 阶段 输入文件 -o 输出文件
```

其中, `输入文件` 为 SysY 文件的路径, `输出文件` 为编译器的输出文件路径, `阶段` 选项可以为:

* `-koopa`: SysY 到 Koopa IR 阶段的功能测试, 此时你的编译器必须向输出文件中输出输入的 SysY 程序编译后的 Koopa IR.
* `-riscv`: SysY 到 RISC-V 阶段的功能测试, 此时你的编译器必须向输出文件中输出输入的 SysY 程序编译后的 RISC-V 汇编.
* `-perf`: 性能测试, 此时你的编译器必须向输出文件中输出输入的 SysY 程序编译后的 RISC-V 汇编.

例如, 你希望使用你的编译器 `compiler` 把文件 `hello.c` 中的 SysY 程序编译成 Koopa IR, 并且保存到文件 `hello.koopa` 中, 你应该执行:

```
./compiler -koopa hello.c -o hello.koopa
```

其他选项类似, 此处不再举例.

## 测试你的编译器

实验环境内附带了自动测试脚本, 名为 `autotest`. 进入命令行后, 你可以执行如下命令来自动编译并测试项目目录中的编译器:

```
autotest 阶段 编译器项目目录
```

其中, `阶段` 选项和编译器命令行中的 `阶段` 选项含义一致.

例如, 你的编译器项目 (只保留项目本身即可, 不需要提前编译) 位于 `/root/compiler`, 你希望测试你的编译器输出的 Koopa IR 的正确性, 你可以执行:

```
autotest -koopa /root/compiler
```

自动测试脚本还支持一些其他的选项, 例如指定使用何种测试用例来测试编译器, 详见自动测试脚本的 [README](https://github.com/pku-minic/compiler-dev/blob/master/autotest/README.md), 或者 `autotest --help` 命令的输出.

此外, 如果只是测试自己的编译器, 你并不需要进入容器的命令行, 你可以直接在宿主机执行:

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest 阶段 /root/compiler
```

## 实验环境中的工具

实验环境中已经配置了如下工具:

* **必要的工具:** `git`, `flex`, `bison`, `python3`.
* **构建工具:** `make`, `cmake`.
* **运行工具:** `qemu-user-static`.
* **编译工具链:** Rust 工具链, LLVM 工具链.
* **Koopa IR 相关工具:** `libkoopa` (Koopa 的 C/C++ 库), `koopac` (Koopa IR 到 LLVM IR 转换器).
* **测试脚本:** `autotest`.

举例:

使用你的编译器生成 Koopa IR, 并运行生成的 Koopa IR:

```
./compiler -koopa hello.c -o hello.koopa
koopac hello.koopa | lli --extra-archive=$CDE_LIBRARY_PATH/native/libsysy.a
```

使用你的编译器生成 RISC-V 汇编代码, 将其汇编为二进制, 并运行生成的二进制:

```
./compiler -riscv hello.c -o hello.S
clang hello.S -c -o hello.o -target riscv32-unknown-linux-elf -march=rv32im -mabi=ilp32
ld.lld hello.o -L$CDE_LIBRARY_PATH/riscv32 -lsysy -o hello
qemu-riscv32-static hello
```
