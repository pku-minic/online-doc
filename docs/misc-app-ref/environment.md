# 实验环境使用说明

## 配置实验环境

见 [Lv0.1 配置 Docker](/lv0-env-config/docker).

## 进入实验环境的命令行

你可以执行如下命令来进入实验环境的命令行:

```
docker run -it --rm maxxing/compiler-dev bash
```

如果你希望把自己的编译器项目目录挂载到容器中 (大部分情况下都需要这么做), 你可以执行:

```
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev bash
```

此时你本地的项目目录会出现在容器的 `/root/compiler` 目录中.

如果你希望在容器中使用调试器 (例如容器内的 `lldb`) 调试程序, 你应该:

```
docker run -it --rm -v 项目目录:/root/compiler \
  --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
  maxxing/compiler-dev bash
```

## 准备你的编译器

为了保证测试的正常进行, 你的编译器必须符合下列要求:

### 项目要求

你可以使用 C/C++/Rust 来实现你的编译器, 同时为了方便测试程序在测试时编译你的编译器项目, 项目的根目录中必须存在下列三种文件之一:

* **`Makefile` 或 `makefile` 文件:**
  * 编译命令行: `make BUILD_DIR="build目录" LIB_DIR="libkoopa目录" INC_DIR="libkoopa头文件目录" -C "项目目录"`.
  * 要求: 你的 `Makefile` 必须依据 `BUILD_DIR` 参数的值, 将生成的可执行文件输出到该目录中, 并命名为 `compiler`. 如果你的编译器依赖 `libkoopa`, 你可以在链接时使用 `LIB_DIR` 和 `INC_DIR` 参数获取 `libkoopa` 及其头文件所在的目录.
* **`CMakeLists.txt` 文件:**
  * 生成编译脚本: `cmake -S "项目目录" -B "build目录" -DLIB_DIR="libkoopa目录" -DINC_DIR="libkoopa头文件目录"`.
  * 编译命令行: `cmake --build "build目录"`.
  * 要求: 你的 `CMakeLists.txt` 必须将可执行文件直接输出到所指定的 `build` 目录的根目录, 且将其命名为 `compiler`. 如果你的编译器依赖 `libkoopa`, 你可以在链接时使用 `LIB_DIR` 和 `INC_DIR` 参数获取 `libkoopa` 及其头文件所在的目录.
* **`Cargo.toml` 文件:**
  * 编译命令行: `cargo build --manifest-path "Cargo.toml的路径" --release`.
  * 要求: 你无需担心任何其他内容.

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
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev \
  autotest 阶段 /root/compiler
```

MaxXing 在开发这套环境时, 常用的测试方法为:

```bash
# 先进入 Docker 容器
docker run -it --rm -v 项目目录:/root/compiler maxxing/compiler-dev bash
# 在容器中运行 autotest, 但指定工作目录 (-w 选项)
# 同时, 使用 tee 命令将输出保存到文件
autotest -w wd compiler 2>&1 | tee compiler/out.txt
# 测试完毕后, 不要退出容器, 回到宿主机修复 bug
# 因为编译器目录已经被挂到了容器里, 所以你能在宿主机看到刚刚生成的 out.txt
# 同时你在宿主机对代码做出的更改也能反映到容器内
# ...
# 修改完成后, 回到容器运行同样的 autotest 命令
# 因为我们指定了工作目录, autotest 会在上次编译的基础上增量编译你的编译器
# 这样能节省很多时间
autotest -w wd compiler 2>&1 | tee compiler/out.txt
```

## 调试你的编译器

在测试编译器的过程中, `autotest` 可能会报告一些错误, 例如 “WRONG ANSWER”, “CASE ASSEMBLE ERROR” 等等. 出现这些错误的原因, 通常是你的编译器在实现上存在问题.

首先你需要知道, `autotest` 在测试你的编译器的过程中, 实际上执行了如下操作:

1. 使用 C/C++/Rust 工具链编译你的编译器.
2. 使用你的编译器编译测试用例.
3. 把你的编译器输出的测试用例汇编并链接成可执行文件.
4. 执行这个可执行文件, 收集执行结果 (程序的 `stdout` 和返回值), 并且和预期结果进行比较.
5. 输出测试结果.

基于上述流程, `autotest` 可能会报告如下错误:

* **输出 C/C++/Rust 的编译错误信息:** 测试脚本未能成功编译你的编译器.
* **CASE COMPILE ERROR:** 测试脚本在调用你的编译器编译测试用例时, 检测到你的编译器发生了错误 (编译器的返回值不为 0), 例如你的编译器崩溃了.
* **CASE COMPILE TIME EXCEEDED:** 测试脚本在调用你的编译器编译测试用例时, 发现你的编译器运行时间过长 (超过 5 分钟).
* **OUTPUT NOT FOUND:** 测试脚本调用你的编译器编译了测试用例, 但发现你的编译器没有把编译结果输出到命令行中指定的文件.
* **CASE ASSEMBLE ERROR:** 测试脚本在把你的编译器编译得到的测试用例, 汇编到可执行文件的过程中, 发生了错误, 通常是因为你的编译器输出了错误的 Koopa IR/RISC-V 汇编.
* **CASE ASSEMBLE TIME EXCEEDED:** 测试脚本在把你的编译器编译得到的测试用例, 汇编到可执行文件的过程中, 发现该流程执行时间过长 (超过 1 分钟), 通常是因为你的编译器输出了一个巨大的文件.
* **TIME LIMIT EXCEEDED:** 测试脚本在运行你的编译器编译得到的测试用例时, 检测到运行时间过长 (超过 2 分钟), 通常是因为你的编译器生成的程序中出现了死循环.
* **WRONG ANSWER:** 测试脚本运行了你的编译器编译得到的测试用例, 但检测到运行结果和预期结果不符.

你可以根据错误的类型, 对你的编译器进行针对性的调试.

需要额外说明的是, `autotest` 在测试你的编译器时所使用的测试用例, 位于 `compiler-dev` 镜像中的 `/opt/bin/testcases` 目录中. 在调试时, 你可以使用你的编译器编译其中的测试用例, 来进一步定位问题发生的原因. 测试用例通常包含以下三类文件:

* **`.c` 文件:** 测试用例本体.
* **同名的 `.out` 文件:** 测试用例的参考输出. 如果该文件只有一行, 则其对应的是程序的预期返回值; 如果文件有多行, 则最后一行是程序的预期返回值, 之前的内容为程序的预期标准输出.
* **同名的 `.in` 文件:** 测试用例的标准输入. 如果测试用例程序中调用了读取标准输入的库函数, 例如 `getint`, `getch` 等, 程序的标准输入会由该文件指定. 如果测试用例程序不会读取标准输入, 则可以不提供 `.in` 文件.

除此之外, `compiler-dev` 镜像中内置的本地测试用例可以在 [GitHub 上找到](https://github.com/pku-minic/compiler-dev-test-cases).

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
koopac hello.koopa | llc --filetype=obj -o hello.o
clang hello.o -L$CDE_LIBRARY_PATH/native -lsysy -o hello
./hello
```

使用你的编译器生成 RISC-V 汇编代码, 将其汇编为二进制, 并运行生成的二进制:

```
./compiler -riscv hello.c -o hello.S
clang hello.S -c -o hello.o -target riscv32-unknown-linux-elf -march=rv32im -mabi=ilp32
ld.lld hello.o -L$CDE_LIBRARY_PATH/riscv32 -lsysy -o hello
qemu-riscv32-static hello
```

如果需要在实验环境中查看程序的返回值, 你可以在运行程序之后, 紧接着在命令行中执行:

```
echo $?
```

比如:

```
qemu-riscv32-static hello; echo $?
```

需要注意的是, 程序的 `main` 函数的返回值类型是 `int`, 即支持返回 32 位的返回值. 但你也许会发现, 你使用 `echo $?` 看到的返回值永远都位于 $[0, 255]$ 的区间内. 这是因为 Docker 实验环境内实际上运行的是 Linux 操作系统, Linux 程序退出时会使用 `exit` 系统调用传递返回值, 但接收返回值的一方可能会使用 `wait`, `waitpid` 等系统调用处理返回值, 此时只有返回值的低 8 位会被保留.
