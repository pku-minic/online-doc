# SysY 运行时库

?> SysY 官方的运行时库规范见[这里](https://gitlab.eduxiji.net/nscscc/compiler2021/-/blob/master/SysY%E8%BF%90%E8%A1%8C%E6%97%B6%E5%BA%93.pdf).
<br><br>
编译实践课所使用的 SysY 运行时库和官方定义略有不同: 实践课的 SysY 使用的计时函数比官方定义更加简单.

SysY 运行时库提供一系列 I/O 函数, 计时函数等用于在 SysY 程序中表达输入/输出, 计时等功能需求. 由于 SysY 并不具备 `include` 和函数声明的语法, 这些库函数无需在 SysY 程序中声明, 即可在 SysY 的 函数中使用.

## 相关文件

我们提供如下和 SysY 运行时库相关的文件:

* `libsysy.a`: 评测时使用的 SysY 运行时库的静态链接库文件.
* `sylib.h`: 其中包含 SysY 运行时库涉及的函数等的声明.
* `sylib.c`: 其中包含 SysY 运行时库涉及的函数等的定义.

?> 评测系统使用的 SysY 源程序中不会出现对 `sylib.h` 文件的包含, 你实现的 SysY 编译器需要正确分析和处理 SysY 程序中对这些函数的调用.

你可以从 [GitHub 上](https://github.com/pku-minic/sysy-runtime-lib/)下载相关的文件.

## I/O 函数

SysY 运行时库提供一系列 I/O 函数, 支持对整数, 字符以及一串整数的输入和输出.

以下未被列出的函数将不会出现在任何 SysY 评测用例中.

### getint

**函数声明**: `int getint()`

**描述**: 从标准输入读取一个整数, 返回对应的整数值.

**示例**:

```clike
int n;
n = getint();
```

### getch

**函数声明**: `int getch()`

**描述**: 从标准输入读取一个字符, 返回字符对应的 ASCII 码值.

**示例**:

```clike
int n;
n = getch();
```

### getarray

**函数声明**: `int getarray(int[])`

**描述**: 从标准输入读取一串整数, 其中第一个整数代表后续出现整数的个数, 该数值通过返回值返回; 后续的整数通过传入的数组参数返回.

?> `getarray` 函数只获取传入数组的起始地址, 而不检查调用者提供的数组是否有足够的空间容纳输入的一串整数.

**示例**:

```clike
int a[10][10];
int n;
n = getarray(a[0]);
```

### putint

**函数声明**: `void putint(int)`

**描述**: 输出一个整数的值.

**示例**:

```clike
int n = 10;
putint(n);
putint(10);
putint(n);
```

将输出: `101010`.

### putch

**函数声明**: `void putch(int)`

**描述**: 将整数参数的值作为 ASCII 码, 输出该 ASCII 码对应的字符.

?> 传入的整数参数取值范围应为 0 到 255, `putch` 不检查参数的合法性.

**示例**:

```clike
int n = 10;
putch(n);
```

将输出换行符.

### putarray

**函数声明**: `void putarray(int, int[])`

**描述**: 第 1 个参数指定了输出整数的个数 (假设为 `N`), 第 2 个参数指向的数组中包含 N 个整数. `putarray` 在输出时会在整数之间安插空格.

?> `putarray` 函数不检查参数的合法性.

**示例**:

```clike
int n = 2;
int a[2] = {2, 3};
putarray(n, a);
```

将输出: `2: 2 3`.

## 计时函数

SysY 运行时库提供 `starttime` 和 `stoptime` “函数”, 用于测量 SysY 中某段代码的运行时间. 在一个 SysY 程序中, 可以插入多对 `starttime`, `stoptime` 调用, 以此来获得每对调用之间的代码的执行时长, 并在 SysY 程序执行结束后得到这些计时的累计执行时长.

你需要注意:

1. `starttime` 和 `stoptime` 只会出现在课程提供的**性能测试用例**中.

2. `starttime`, `stoptime` 不支持嵌套调用的形式, 即不支持:

    ```clike
    starttime();
    ...
    starttime();
    ...
    stoptime();
    ...
    stoptime();
    ```

    这样的调用执行序列.

下面分别介绍所提供的计时函数的访问接口.

### starttime

**函数声明**: `void starttime()`.

**描述**: 开启计时器. 此函数应和 `stoptime()` 联用.

### stoptime

**函数声明**: `void stoptime()`.

**描述**: 停止计时器. 此函数应和 `starttime()` 联用.

程序会在最后结束的时候, 整体输出每个计时器所花费的时间, 并统计所有计时器的累计值. 格式为 `Timer#编号: 时-分-秒-微秒`.

**示例**:

```clike
void foo(int n) {
  starttime();
  int i = 0;
  while (i < n) {
    // do something...
    i = i + 1;
  }
  stoptime();
}

int main() {
  starttime();
  int i = 0;
  while (i < 3) {
    // do something...
    i = i + 1;
  }
  stoptime();
  foo(2);
  return 0;
}
```

输出 (仅作示例):

```
Timer#001: 0H-0M-3S-3860us
Timer#002: 0H-0M-2S-2660us
TOTAL: 0H-0M-5S-6520us
```
